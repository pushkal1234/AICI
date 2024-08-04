import re

import langid
from langchain_community.llms import Ollama
import nltk
from nltk.corpus import words


class TranslationController:
    def __init__(self, model):
        self.model = model
        nltk.download('words')
        self.english_words = set(words.words())

    def remove_extra(self, text):
        chars_to_remove = ['"', "'", ':']
        for char in chars_to_remove:
            text = text.replace(char, '')
        return text

    def check_multiline_and_german(self, output_translation):
        """
        Checks english content at line level
        """
        
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
    
    def repeat_translation(self, output_translation, llm, final_prompt):
        while output_translation is None:
            output_translation = llm.invoke(final_prompt, stop=['.'])
        
        return output_translation
    
    def check_english_content(self, output_translation):
        """
        Checks english content at word level
        """
        output_translation = re.sub(r'[^a-zA-ZäöüÄÖÜß\s]', '', output_translation)
        print("I am here")
        words = output_translation.split()
        print(words)
        german_filtered_words = [word for word in words if word.lower() not in self.english_words]
        return ' '.join(german_filtered_words)


    def get_translation_from_LLM(self, input_text):
        import utils
        
        prompt = utils.load_prompt()
        final_prompt = f"Translate '{input_text}' to german. " + prompt["translate_prompt"]

        print(final_prompt)
        llm = Ollama(model=self.model, temperature=0)
        output_translation = llm.invoke(final_prompt, stop=['.'])
        if output_translation is None:
            output_translation = self.repeat_translation(output_translation, llm, final_prompt)
              
        print("first", output_translation)
        output_translation = self.check_multiline_and_german(output_translation)
        if output_translation is None:
            output_translation = self.repeat_translation(output_translation, llm, final_prompt)
        
        print("After multiline check", output_translation)
        output_translation = self.check_english_content(output_translation)
        
        return output_translation

    def input_preprocess(self, input_text):
        sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s')
        sentences = sentence_endings.split(input_text)
        return [sentence.strip() for sentence in sentences if sentence]

    def generate_translation(self, input_text):
        sentence_list = self.input_preprocess(input_text)
        print(sentence_list)

        german_translation_list = []
        for index in range(len(sentence_list)):
            print("-----------")
            german_translation = self.get_translation_from_LLM(sentence_list[index])
            print(german_translation)
            german_translation_list.append(german_translation)
            if not german_translation.endswith(('.', '!', '?', '...', '"', "'", ')', ';', ':')):
                german_translation_list.append('.')

        return ''.join(german_translation_list)
    

    