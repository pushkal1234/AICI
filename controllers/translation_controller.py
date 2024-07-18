import re

import langid
from langchain_community.llms import Ollama


class TranslationController:
    def __init__(self, model):
        self.model = model

    def remove_extra(self, text):
        chars_to_remove = ['"', "'", ':']
        for char in chars_to_remove:
            text = text.replace(char, '')
        return text

    def check_multiline_and_german(self, output_translation):
        output_multiline_length = len(output_translation.split('\n'))
        if output_multiline_length > 1:
            multiline_split = output_translation.split('\n')
            for line in multiline_split:
                language, _ = langid.classify(line)
                if language == 'de':
                    cleaned_line = self.remove_extra(line)
                    return cleaned_line
        else:
            output_translation = self.remove_extra(output_translation)
            return output_translation

    def get_translation_from_LLM(self, input_text):
        initial_prompt = "Translate to german"
        final_prompt = f'"{input_text}". {initial_prompt}'

        print(final_prompt)

        llm = Ollama(model=self.model, temperature=0)
        output_translation = llm.invoke(final_prompt, stop=['.'])
        output_translation = self.check_multiline_and_german(output_translation)

        return output_translation

    def input_preprocess(self, input_text):
        sentence_list = re.split(r'(?<=[.!?]) +', input_text)
        return sentence_list

    def generate_translation(self, input_text):
        sentence_list = self.input_preprocess(input_text)

        german_translation_list = []
        for index in range(len(sentence_list)):
            print("-----------")
            german_translation = self.get_translation_from_LLM(sentence_list[index])
            german_translation_list.append(german_translation)
            german_translation_list.append('.')

        return ''.join(german_translation_list)

