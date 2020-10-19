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
from tempfile import NamedTemporaryFile

import streamlit as st
from annotated_text import annotated_text
from kiwi import load_system
from kiwi.constants import BAD, OK
from streamlit.uploaded_file_manager import UploadedFile

from kiwi_tasting.predefined_data import (
    sentence_hter,
    source_sentences,
    target_sentences,
    word_tags,
)

predefined_lines = {
    'source': source_sentences,
    'target': target_sentences,
    'tags': word_tags,
    'scores': sentence_hter,
}


@st.cache(allow_output_mutation=True)
def read_lines(uploaded_file):
    return [line.decode("utf-8").strip() for line in uploaded_file.readlines()]


def probability_to_rgb(probability: float):
    red = min(255, int(2 * probability * 255))
    green = min(255, int(2 * (1 - probability) * 255))
    return f'rgb({red}, {green}, 90)'


@st.cache(
    hash_funcs={UploadedFile: lambda x: x.id},
    allow_output_mutation=True,
    show_spinner=True,
)
def load_model(uploaded_file):
    model = None
    if uploaded_file:
        temp_file = NamedTemporaryFile(delete=False)
        temp_file.write(uploaded_file.read())
        temp_file.close()

        model = load_system(temp_file.name)

        Path(temp_file.name).unlink()

    return model


def main():
    st.beta_set_page_config(
        page_title='Kiwi Tasting - OpenKiwi demonstration',
        page_icon='./assets/img/logo.ico',
        initial_sidebar_state='expanded',
        layout='wide',
    )

    st.sidebar.image(
        ".`/assets/img/openkiwi-logo-horizontal.png", use_column_width=True
    )
    st.sidebar.title("Kiwi Tasting")
    st.sidebar.markdown("Inspect predictions by OpenKiwi.")
    st.sidebar.markdown(
        "[paper](https://www.aclweb.org/anthology/P19-3020/) | "
        "[code](https://github.com/Unbabel/OpenKiwi)"
    )
    st.sidebar.markdown("---")

    st.sidebar.header("QE Models")
    uploaded_files = st.sidebar.file_uploader(
        "Load a pretrained QE Model", accept_multiple_files=True
    )
    models = {}
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in models:
            new_model = load_model(uploaded_file)
            models[uploaded_file.name] = new_model
    st.sidebar.write('Select loaded models to use')
    selected_models = {}
    if not models:
        st.sidebar.write('No model loaded')
    else:
        for name in models:
            selected_models[name] = st.sidebar.checkbox(name, True)
    st.sidebar.markdown("---")

    st.sidebar.header("Input")
    st.sidebar.write("Specify paths to input data.")
    lines = {}
    source_path = st.sidebar.file_uploader("Source sentences")
    target_path = st.sidebar.file_uploader("Target sentences")
    if source_path:
        lines['source'] = read_lines(source_path)
    if target_path:
        lines['target'] = read_lines(target_path)

    st.sidebar.subheader('Gold input (if no model is provided)')
    tags_path = st.sidebar.file_uploader("Tags")
    probs_path = st.sidebar.file_uploader("Probabilities")
    scores_path = st.sidebar.file_uploader("Sentences HTER (scores)")
    if tags_path:
        lines['tags'] = read_lines(tags_path)
        st.sidebar.write('tags:', len(lines['tags']))
    if probs_path:
        lines['probs'] = read_lines(probs_path)
    if scores_path:
        lines['scores'] = read_lines(scores_path)

    if not lines:
        lines = predefined_lines

    # ---------------------------------------------------------------------------------
    st.header("Build a translation pair")
    st.write(
        "Select a predefined source sentence and/or edit both source and target sentences."
    )

    source_sentence = target_sentence = ''
    i = None
    if 'source' in lines:
        i = lines['source'].index(
            st.selectbox(
                "Choose a predefined source sentence to display",
                options=lines['source'],
            )
        )
        source_sentence = lines['source'][i]
        if 'target' in lines:
            target_sentence = lines['target'][i]

    col1, col2 = st.beta_columns(2)
    with col1:
        source = st.text_area('Source sentence', value=source_sentence)
    with col2:
        target = st.text_area('Target sentence', value=target_sentence)

    st.header('Quality Estimation')
    if selected_models:
        use_models = [name for name, selected in selected_models.items() if selected]
        for model_name in use_models:
            model = models[model_name]
            st.subheader(
                f'Using model: {model.system.__class__.__name__} ({model_name})'
            )

            prediction = model.predict([source], [target])
            probs = prediction.target_tags_BAD_probabilities[0]
            tags = prediction.target_tags_labels[0]

            if prediction.sentences_hter:
                hter = prediction.sentences_hter[0]
                st.write('Sentence fixing effort (HTER): ', hter)

            target_tokens = target.split()
            if tags and probs:
                text = [
                    (token, tag, probability_to_rgb(prob))
                    for token, tag, prob in zip(target_tokens, tags, probs)
                ]
                annotated_text(*text)
    if i is not None:
        st.subheader('Using predefined data')
        target_tokens = lines['target'][i].split()
        tags = probs = hter = None
        if 'probs' in lines:
            probs = lines['probs'][i]
            tags = [OK if int(prob <= 0.5) == 0 else BAD for prob in probs]
        elif 'tags' in lines:
            tags = lines['tags'][i].split()
            if len(tags) == 2 * len(target_tokens) + 1:
                tags = tags[1::2]
            probs = [1.0 if tag == BAD else 0.0 for tag in tags]
        else:
            st.error(
                'No model and no gold data specified; cannot render quality scores'
            )
        if 'scores' in lines:
            hter = lines['scores'][i]

        if hter:
            st.write('Sentence fixing effort (HTER): ', hter)

        if tags and probs:
            text = [
                (token, tag, probability_to_rgb(prob))
                for token, tag, prob in zip(target_tokens, tags, probs)
            ]
            annotated_text(*text)
    else:
        st.error('No model and no gold data specified; cannot render quality scores')


if __name__ == "__main__":
    main()
