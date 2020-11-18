"""
Utilities for working with the local dataset cache.

This file is adapted from the HuggingFace Transformers library at
https://github.com/huggingface/transformers, which itself adapts over the AllenNLP
library at https://github.com/allenai/allennlp.
Copyright by the AllenNLP authors.
"""
import fnmatch
import io
import json
import logging
import os
import shutil
import tarfile
import tempfile
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Dict, Optional, Union
from urllib.parse import urlparse
from zipfile import ZipFile, is_zipfile

import requests
from filelock import FileLock
from transformers import TRANSFORMERS_CACHE
from transformers.file_utils import (
    http_get,
    http_user_agent,
    is_remote_url,
    url_to_filename,
)


def cached_path(
    url_or_filename,
    cache_dir=None,
    force_download=False,
    proxies=None,
    resume_download=False,
    user_agent: Union[Dict, str, None] = None,
    extract_compressed_file=False,
    force_extract=False,
    local_files_only=False,
) -> Optional[str]:
    """
    Given something that might be a URL (or might be a local path), determine which.
    If it's a URL, download the file and cache it, and return the path to the cached
    file. If it's already a local path, make sure the file exists and then return the
    path.

    Args:
        cache_dir: specify a cache directory to save the file to (overwrite the default
            cache dir).
        force_download: if True, re-download the file even if it's already cached in
            the cache dir.
        resume_download: if True, resume the download if incompletely received file is
            found.
        user_agent: Optional string or dict that will be appended to the user-agent on
            remote requests.
        extract_compressed_file: if True and the path point to a zip or tar file,
            extract the compressed file in a folder along the archive.
        force_extract: if True when extract_compressed_file is True and the archive was
            already extracted, re-extract the archive and override the folder where it
            was extracted.

    Return:
        Local path (string) of file or if networking is off, last version of file
        cached on disk.

    Raises:
        In case of non-recoverable file (non-existent or inaccessible url + no cache on
        disk).
    """
    if cache_dir is None:
        cache_dir = TRANSFORMERS_CACHE
    if isinstance(url_or_filename, Path):
        url_or_filename = str(url_or_filename)
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    if is_remote_url(url_or_filename):
        # URL, so get it from the cache (downloading if necessary)
        output_path = get_from_cache(
            url_or_filename,
            cache_dir=cache_dir,
            force_download=force_download,
            proxies=proxies,
            resume_download=resume_download,
            user_agent=user_agent,
            local_files_only=local_files_only,
        )
    elif os.path.exists(url_or_filename):
        # File, and it exists.
        output_path = url_or_filename
    elif urlparse(url_or_filename).scheme == "":
        # File, but it doesn't exist.
        raise EnvironmentError("file {} not found".format(url_or_filename))
    else:
        # Something unknown
        raise ValueError(
            "unable to parse {} as a URL or as a local path".format(url_or_filename)
        )

    if extract_compressed_file:
        if not is_zipfile(output_path) and not tarfile.is_tarfile(output_path):
            return output_path

        # Path where we extract compressed archives
        # We avoid '.' in dir name and add "-extracted" at the end:
        # "./model.zip" => "./model-zip-extracted/"
        output_dir, output_file = os.path.split(output_path)
        output_extract_dir_name = output_file.replace(".", "-") + "-extracted"
        output_path_extracted = os.path.join(output_dir, output_extract_dir_name)

        if (
            os.path.isdir(output_path_extracted)
            and os.listdir(output_path_extracted)
            and not force_extract
        ):
            return output_path_extracted

        # Prevent parallel extractions
        lock_path = output_path + ".lock"
        with FileLock(lock_path):
            shutil.rmtree(output_path_extracted, ignore_errors=True)
            os.makedirs(output_path_extracted)
            if is_zipfile(output_path):
                with ZipFile(output_path, "r") as zip_file:
                    zip_file.extractall(output_path_extracted)
                    zip_file.close()
            elif tarfile.is_tarfile(output_path):
                tar_file = tarfile.open(output_path)
                tar_file.extractall(output_path_extracted)
                tar_file.close()
            else:
                raise EnvironmentError(
                    "Archive format of {} could not be identified".format(output_path)
                )

        return output_path_extracted

    return output_path


def get_from_cache(
    url: str,
    cache_dir=None,
    force_download=False,
    proxies=None,
    etag_timeout=10,
    resume_download=False,
    user_agent: Union[Dict, str, None] = None,
    local_files_only=False,
) -> Optional[str]:
    """
    Given a URL, look for the corresponding file in the local cache. If it's not there,
    download it. Then return the path to the cached file.

    Modification from original method at
    https://github.com/huggingface/transformers/blob/v3.5.1/src/transformers/file_utils.py:  # NoQA
        * Do not raise exception if there's no ETag in the header; we need this in
          order to be able to download assets in a GitHub release

    Return:
        Local path (string) of file or if networking is off, last version of file
        cached on disk.

    Raises:
        In case of non-recoverable file (non-existent or inaccessible url + no cache on
        disk).
    """
    if cache_dir is None:
        cache_dir = TRANSFORMERS_CACHE
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    os.makedirs(cache_dir, exist_ok=True)

    url_to_download = url
    etag = None
    if not local_files_only:
        try:
            headers = {"user-agent": http_user_agent(user_agent)}
            r = requests.head(
                url,
                headers=headers,
                allow_redirects=False,
                proxies=proxies,
                timeout=etag_timeout,
            )
            r.raise_for_status()
            etag = r.headers.get("X-Linked-Etag") or r.headers.get("ETag")
            # We favor a custom header indicating the etag of the linked resource, and
            # we fallback to the regular etag header.
            # If we don't have any of those, raise an error.
            if etag is None:
                logging.warning(
                    "Distant resource does not have an ETag, we won't be able to "
                    "reliably ensure reproducibility."
                )
                etag = ""  # Just keep going
            # In case of a redirect,
            # save an extra redirect on the request.get call,
            # and ensure we download the exact atomic version even if it changed
            # between the HEAD and the GET (unlikely, but hey).
            if 300 <= r.status_code <= 399:
                url_to_download = r.headers["Location"]
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # etag is already None
            pass

    filename = url_to_filename(url, etag)

    # get cache path to put the file
    cache_path = os.path.join(cache_dir, filename)

    # etag is None == we don't have a connection or we passed local_files_only.
    # try to get the last downloaded one
    if etag is None:
        if os.path.exists(cache_path):
            return cache_path
        else:
            matching_files = [
                file
                for file in fnmatch.filter(
                    os.listdir(cache_dir), filename.split(".")[0] + ".*"
                )
                if not file.endswith(".json") and not file.endswith(".lock")
            ]
            if len(matching_files) > 0:
                return os.path.join(cache_dir, matching_files[-1])
            else:
                # If files cannot be found and local_files_only=True,
                # the models might've been found if local_files_only=False
                # Notify the user about that
                if local_files_only:
                    raise ValueError(
                        "Cannot find the requested files in the cached path and "
                        "outgoing traffic has been disabled. To enable model look-ups "
                        "and downloads online, set 'local_files_only' to False."
                    )
                else:
                    raise ValueError(
                        "Connection error, and we cannot find the requested files in "
                        "the cached path. Please try again or make sure your Internet "
                        "connection is on."
                    )

    # From now on, etag is not None.
    if os.path.exists(cache_path) and not force_download:
        return cache_path

    # Prevent parallel downloads of the same file with a lock.
    lock_path = cache_path + ".lock"
    with FileLock(lock_path):

        # If the download just completed while the lock was activated.
        if os.path.exists(cache_path) and not force_download:
            # Even if returning early like here, the lock will be released.
            return cache_path

        if resume_download:
            incomplete_path = cache_path + ".incomplete"

            @contextmanager
            def _resumable_file_manager() -> "io.BufferedWriter":
                with open(incomplete_path, "ab") as f:
                    yield f

            temp_file_manager = _resumable_file_manager
            if os.path.exists(incomplete_path):
                resume_size = os.stat(incomplete_path).st_size
            else:
                resume_size = 0
        else:
            temp_file_manager = partial(
                tempfile.NamedTemporaryFile, mode="wb", dir=cache_dir, delete=False
            )
            resume_size = 0

        # Download to temporary file, then copy to cache dir once finished.
        # Otherwise you get corrupt cache entries if the download gets interrupted.
        with temp_file_manager() as temp_file:
            logging.info(
                "%s not found in cache or force_download set to True, downloading to "
                "%s",
                url,
                temp_file.name,
            )

            http_get(
                url_to_download,
                temp_file,
                proxies=proxies,
                resume_size=resume_size,
                user_agent=user_agent,
            )

        logging.info("storing %s in cache at %s", url, cache_path)
        os.replace(temp_file.name, cache_path)

        logging.info("creating metadata file for %s", cache_path)
        meta = {"url": url, "etag": etag}
        meta_path = cache_path + ".json"
        with open(meta_path, "w") as meta_file:
            json.dump(meta, meta_file)

    return cache_path
