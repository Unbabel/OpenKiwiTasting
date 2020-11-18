#  OpenKiwi: Open-Source Machine Translation Quality Estimation
#  Copyright (C) 2020 Unbabel <openkiwi@unbabel.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from pathlib import Path
from typing import Any, Dict, Optional, Union

from kiwi.data.datasets.wmt_qe_dataset import read_file
from omegaconf import OmegaConf
from pydantic import BaseModel, BaseSettings, Extra, validator
from pydantic.types import DirectoryPath, FilePath


class DataFields(BaseModel):
    directory: Optional[DirectoryPath] = None
    source: FilePath
    target: FilePath
    sentence_scores: FilePath
    target_tags: FilePath
    source_tags: Optional[FilePath] = None

    @validator('directory', pre=True, allow_reuse=True)
    def anchor_given_directory(cls, v):
        if v:
            if not Path(v).is_absolute():
                v = Path.cwd() / v
        return v

    @validator(
        'source',
        'target',
        'sentence_scores',
        'target_tags',
        'source_tags',
        pre=True,
        allow_reuse=True,
    )
    def anchor_to_directory(cls, v, values, field):
        if v is not None and values.get('directory') is not None:
            if not Path(v).is_absolute():
                v = values['directory'] / v
        return v


class DataSettings(BaseSettings):
    data: Dict[str, DataFields]

    def __init__(
        __pydantic_self__,
        config: Optional[Union[str, Path]] = Path(__file__).parent / '../data.yaml',
        **data: Any
    ) -> None:
        if config is not None:
            config_path = Path(config).expanduser()
            config_dict = OmegaConf.load(config_path.open())
            if config_dict:
                data_config = OmegaConf.merge(config_dict, OmegaConf.create(data))
                data = OmegaConf.to_container(data_config)
        super().__init__(**data)

    class Config:
        # Throws an error whenever an extra key is provided, effectively making parsing
        # strict
        extra = Extra.forbid


class Dataset:
    def __init__(self, config: DataFields):
        self.source_sentences = read_file(config.source, None)
        self.target_sentences = read_file(config.target, None)
        self.sentence_scores = read_file(config.sentence_scores, None)
        self.target_tags = read_file(config.target_tags, None)
        self.source_tags = None
        if config.source_tags:
            self.source_tags = read_file(config.source_tags, None)
