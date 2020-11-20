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

import pandas
import streamlit as st
from annotated_text import annotated_text
from kiwi import load_system
from kiwi.constants import BAD

from kiwi_tasting.data import Dataset, DataSettings
from kiwi_tasting.file_utils import cached_path
from kiwi_tasting.models import ModelsSettings


def probability_to_rgb(probability: float):
    red = min(255, int(2 * probability * 255))
    green = min(255, int(2 * (1 - probability) * 255))
    return f'rgb({red}, {green}, 90)'


def anchor_path(path, anchor_dir=None) -> str:
    if not anchor_dir:
        anchor_dir = Path(__file__).parent
    else:
        anchor_dir = Path(anchor_dir)

    return str((anchor_dir / path).resolve())


@st.cache(
    allow_output_mutation=True,
    show_spinner=False,
    max_entries=1,
    suppress_st_warning=True,
)
def retrieve_model(path):
    if path:
        with st.spinner('Downloading pre-trained model...'):
            local_path = cached_path(path, resume_download=True)
        with st.spinner('Loading model...'):
            return load_system(local_path)
    return None


# Keep the state between actions
@st.cache(allow_output_mutation=True)
def current_sentence_state():
    return {"index": 0}


def highlight(s, index, color='yellow'):
    if s.name == index:
        hl = f"background-color: {color}"
    else:
        hl = ""
    return [hl] * len(s)


def main():
    model_settings = ModelsSettings()
    data_settings = DataSettings()
    datasets = {lp: Dataset(config) for lp, config in data_settings.data.items()}

    st.beta_set_page_config(
        page_title='Kiwi Tasting - OpenKiwi demonstration',
        page_icon=anchor_path('./assets/img/logo.ico'),
        initial_sidebar_state='expanded',
        layout='wide',
    )

    st.sidebar.image(
        anchor_path("./assets/img/openkiwi-logo-horizontal.png"), use_column_width=True
    )
    st.sidebar.title("Kiwi Tasting")
    st.sidebar.markdown("Inspect predictions by OpenKiwi.")
    st.sidebar.markdown(
        "[paper](https://www.aclweb.org/anthology/P19-3020/) | "
        "[code](https://github.com/Unbabel/OpenKiwi)"
    )
    st.sidebar.markdown("---")

    st.sidebar.header("Available QE Models")
    selected_model = st.sidebar.radio(
        'Select a pretrained model to use',
        ['None'] + list(model_settings.models.keys()),
        # format_func=lambda model_option:
        # f"{model_option} ({model_settings.models[model_option].LP})",
    )

    if selected_model != 'None':
        loaded_model = retrieve_model(model_settings.models[selected_model].URL)
        use_models = {selected_model: loaded_model}
    else:
        use_models = {}
    st.sidebar.markdown("---")

    st.sidebar.header("Available datasets")
    selected_dataset_name = st.sidebar.radio(
        'Select a dataset to use', list(datasets.keys())
    )

    use_dataset: Dataset = datasets[selected_dataset_name]

    # ---------------------------------------------------------------------------------
    st.header("Build a translation pair")
    st.write(
        "Select a predefined source sentence and/or edit both source and target "
        "sentences."
    )

    source_sentence = target_sentence = ''
    gold_sentence_scores = gold_target_tags = gold_source_tags = None
    if use_dataset:
        df = pandas.DataFrame(
            {
                'source': use_dataset.source_sentences,
                'target': use_dataset.target_sentences,
            }
        )

        current_state = current_sentence_state()

        col1, col2, *_ = st.beta_columns(12)
        with col1:
            previous_pressed = st.button('Previous')
        with col2:
            next_pressed = st.button('Next')

        if previous_pressed:
            current_state['index'] = max(0, current_state['index'] - 1)
        if next_pressed:
            current_state['index'] = min(len(df), current_state['index'] + 1)

        i = st.slider(
            'Scroll through dataset',
            min_value=0,
            max_value=len(use_dataset.source_sentences),
            value=current_state['index'],
        )
        current_state['index'] = i

        source_sentence = use_dataset.source_sentences[i]
        target_sentence = use_dataset.target_sentences[i]
        gold_sentence_scores = use_dataset.sentence_scores[i]
        gold_target_tags = use_dataset.target_tags[i]
        if use_dataset.source_tags:
            gold_source_tags = use_dataset.source_tags[i]

        with st.beta_expander('Preview sentences', expanded=False):
            first_idx = max(i - 7, 0)
            last_idx = min(first_idx + 15, len(use_dataset.source_sentences))
            df_w = df.iloc[first_idx:last_idx].style.apply(highlight, index=i, axis=1)
            st.dataframe(df_w, width=None, height=400)

    st.write('### Edit sentences')
    col1, col2 = st.beta_columns(2)
    with col1:
        source = st.text_area('Source sentence', value=source_sentence)
    with col2:
        target = st.text_area('Target sentence', value=target_sentence)

    st.header('Quality Estimation')
    show_source = st.checkbox('Show source side', value=False)
    for model_name, model in use_models.items():
        st.subheader(f'Using model: {model.system.__class__.__name__} ({model_name})')

        prediction = model.predict([source], [target])

        predicted_target_probabilities = prediction.target_tags_BAD_probabilities[0]
        predicted_target_tags = prediction.target_tags_labels[0]

        predicted_source_probabilities = predicted_source_tags = None
        if prediction.source_tags_labels:
            predicted_source_probabilities = prediction.source_tags_BAD_probabilities[0]
            predicted_source_tags = prediction.source_tags_labels[0]

        if prediction.sentences_hter:
            hter = prediction.sentences_hter[0]
            st.write('Target sentence fixing effort (HTER): ', hter)

        if show_source:
            col1, col2 = st.beta_columns(2)
            with col1:
                source_side = st.beta_container()
            with col2:
                target_side = st.beta_container()
        else:
            target_side = st.beta_container()
            source_side = None

        with target_side:
            if predicted_target_tags and predicted_target_probabilities:
                target_tokens = target.split()
                text = [
                    (token, tag, probability_to_rgb(prob))
                    for token, tag, prob in zip(
                        target_tokens,
                        predicted_target_tags,
                        predicted_target_probabilities,
                    )
                ]
                st.write('Target tags')
                annotated_text(*text)
            else:
                st.write('No target tags prediction')
        if source_side:
            with source_side:
                if predicted_source_tags and predicted_source_probabilities:
                    source_tokens = source.split()
                    text = [
                        (token, tag, probability_to_rgb(prob))
                        for token, tag, prob in zip(
                            source_tokens,
                            predicted_source_tags,
                            predicted_source_probabilities,
                        )
                    ]
                    st.write('Source tags')
                    annotated_text(*text)
                else:
                    st.write('No source tags prediction')

    if gold_target_tags or gold_sentence_scores:
        st.subheader('From dataset')
        if gold_sentence_scores:
            hter = float(gold_sentence_scores.strip())
            st.write('Target sentence fixing effort (HTER): ', hter)

        if show_source:
            col1, col2 = st.beta_columns(2)
            with col1:
                source_side = st.beta_container()
            with col2:
                target_side = st.beta_container()
        else:
            target_side = st.beta_container()
            source_side = None

        with target_side:
            if gold_target_tags:
                target_tokens = target_sentence.split()
                predicted_target_tags = gold_target_tags.split()
                if len(predicted_target_tags) == 2 * len(target_tokens) + 1:
                    predicted_target_tags = predicted_target_tags[1::2]
                predicted_target_probabilities = [
                    1.0 if tag == BAD else 0.0 for tag in predicted_target_tags
                ]
                text = [
                    (token, tag, probability_to_rgb(prob))
                    for token, tag, prob in zip(
                        target_tokens,
                        predicted_target_tags,
                        predicted_target_probabilities,
                    )
                ]
                st.write('Target tags')
                annotated_text(*text)
            else:
                st.write('No gold target tags specified')
        if source_side:
            with source_side:
                if gold_source_tags:
                    source_tokens = source_sentence.split()
                    source_tags = gold_source_tags.split()
                    if len(source_tags) == 2 * len(source_tokens) + 1:
                        source_tags = source_tags[1::2]
                    source_probabilities = [
                        1.0 if tag == BAD else 0.0 for tag in source_tags
                    ]
                    text = [
                        (token, tag, probability_to_rgb(prob))
                        for token, tag, prob in zip(
                            source_tokens, source_tags, source_probabilities
                        )
                    ]
                    st.write('Source tags')
                    annotated_text(*text)
                else:
                    st.write('No gold source tags specified')
    else:
        st.error('No gold data specified; cannot render tags and quality scores')


if __name__ == "__main__":
    main()
