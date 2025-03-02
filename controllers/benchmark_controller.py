import time
from datetime import datetime
from typing import Dict, Any, List
from langchain.llms import Ollama
import tiktoken
import json
import os
import re

class BenchmarkController:
    def __init__(self):
        self.results = []
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, str]:
        """Load model configuration from config.json"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
            with open(config_path, 'r') as config_file:
                return json.load(config_file)
        except Exception as e:
            print(f"Error loading config.json: {str(e)}")
            return {}
    
    def _get_model_name(self, model_key: str) -> str:
        """Get the actual model name from config based on the key"""
        if model_key in self.config:
            return self.config[model_key]
        # If model_key is not in config, return it as is (might be a direct model name)
        return model_key
        
    def _generate_raw_response(self, text: str, task_type: str, model: str, target_language: str = "german") -> tuple:
        """Generate response without controller"""
        start_time = time.time()
        retries = 0
        
        try:
            # Get the actual model name from config
            model_name = self._get_model_name(model)
            llm = Ollama(model=model_name, temperature=0)
            
            # Basic prompt based on task
            prompts = {
                "translation": {
                    "german": "Translate the following English text to German. Return ONLY the translated text without any explanations, notes, or the original text: ",
                    "spanish": "Translate the following English text to Spanish. Return ONLY the translated text without any explanations, notes, or the original text: "
                },
                "sql": "Generate SQL query for the following requirement. Return ONLY the SQL query without any explanations or comments: ",
                "json": "Convert this text to JSON. Return ONLY the JSON without any explanations or comments: ",
                "sentiment": "Analyze the sentiment of each sentence in the given text. Return ONLY a JSON object with counts: {positive:count, negative:count, neutral:count}" 
            }
            
            # Construct the prompt based on task type
            if task_type == "translation":
                # Use the appropriate translation prompt based on target language
                if target_language.lower() in prompts["translation"]:
                    prompt = prompts["translation"][target_language.lower()]
                else:
                    # Default to German if target language not supported
                    prompt = prompts["translation"]["german"]
                final_prompt = f"{prompt}{text}"
            else:
                # For non-translation tasks
                final_prompt = f"{prompts[task_type]}{text}"
            
            response = llm.invoke(final_prompt)
            
            # Calculate tokens
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            input_tokens = len(encoding.encode(text))
            output_tokens = len(encoding.encode(response))
            
            end_time = time.time()
            
            return {
                "response": response,
                "time_taken": end_time - start_time,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens
                },
                "retries": retries,
                "model_used": model_name,  # Include the actual model name used
                "target_language": target_language if task_type == "translation" else None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "time_taken": time.time() - start_time,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "retries": retries,
                "model_used": self._get_model_name(model),  # Include the model name even on error
                "target_language": target_language if task_type == "translation" else None
            }

    def _generate_controlled_response(self, text: str, task_type: str, model: str, controller, target_language: str = "german") -> dict:
        """Generate response with controller"""
        start_time = time.time()
        
        try:
            # Get the actual model name from config
            model_name = self._get_model_name(model)
            
            if task_type == "translation":
                input_data = {"text": text, "target_language": target_language, "model": model_name}
                response, tokens = controller.generate_translation(input_data)
            elif task_type == "sql":
                input_data = {"text": text, "model": model_name}
                response, tokens = controller.generate_sql_query(input_data)
            elif task_type == "json":
                # Add required fields for JSON processing
                input_data = {
                    "text": text,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "model": model_name,
                    "schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "date": { "type": "string", "format": "date" },
                            "users": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": { "type": "string" },
                                        "salary": { "type": "integer", "minimum": 0 },
                                        "expenses": { "type": "integer", "minimum": 0 },
                                        "investments": {
                                            "type": "object",
                                            "additionalProperties": { "type": "integer", "minimum": 0 }
                                        },
                                        "debts": {
                                            "type": "object",
                                            "additionalProperties": { "type": "integer", "minimum": 0 }
                                        },
                                        "loans": {
                                            "type": "object",
                                            "additionalProperties": { "type": "integer", "minimum": 0 }
                                        },
                                        "savings": { "type": "integer", "minimum": 0 }
                                    },
                                    "required": ["name", "salary", "expenses"]
                                }
                            }
                        },
                        "required": ["date", "users"]
                    }
                }
                response, tokens = controller.process_financial_data(input_data)
            elif task_type == "sentiment":
                # Pass model to sentiment controller
                response, tokens = controller.generate_sentiment(text, model_name)
            
            end_time = time.time()
            time_taken_seconds = end_time - start_time
            
            return {
                "response": response,
                "time_taken": round(time_taken_seconds, 3),
                "time_unit": "seconds",
                "tokens": {
                    "total": tokens,
                    "input": len(text.split()),
                    "output": tokens - len(text.split())
                },
                "retries": len(controller.total_output_list) - 1 if hasattr(controller, 'total_output_list') else 0,
                "model_used": model_name,  # Include the actual model name used
                "target_language": target_language if task_type == "translation" else None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "time_taken": time.time() - start_time,
                "time_unit": "seconds",
                "tokens": {"input": 0, "output": 0, "total": 0},
                "retries": 0,
                "model_used": self._get_model_name(model),  # Include the model name even on error
                "target_language": target_language if task_type == "translation" else None
            }

    def run_benchmark(self, test_cases: List[Dict[str, Any]], model: str = "phi3", target_language: str = "german") -> Dict[str, Any]:
        """Run benchmarks for both controlled and raw approaches"""
        # Get the actual model name from config
        model_name = self._get_model_name(model)
        
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "model_key": model,
            "model_used": model_name,
            "target_language": target_language,
            "results": []
        }
        
        for test in test_cases:
            result = {
                "task_type": test["type"],
                "input": test["text"],
                "raw": self._generate_raw_response(test["text"], test["type"], model, target_language),
                "controlled": self._generate_controlled_response(
                    test["text"], 
                    test["type"], 
                    model,
                    test["controller"],
                    target_language
                )
            }
            benchmark_results["results"].append(result)
            
        # Calculate aggregated metrics
        benchmark_results["metrics"] = self._calculate_metrics(benchmark_results["results"])
        
        # Save results
        self._save_results(benchmark_results)
        return benchmark_results

    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comparative metrics"""
        metrics = {
            "average_improvement": {
                "time": 0,
                "tokens": 0,
                "retries": 0
            },
            "task_specific": {}
        }
        
        for result in results:
            task = result["task_type"]
            if task not in metrics["task_specific"]:
                metrics["task_specific"][task] = {
                    "time_improvement": 0,
                    "token_reduction": 0,
                    "retry_reduction": 0,
                    "count": 0
                }
                
            # Calculate improvements
            time_diff = result["raw"]["time_taken"] - result["controlled"]["time_taken"]
            token_diff = result["raw"]["tokens"]["total"] - result["controlled"]["tokens"]["total"]
            retry_diff = result["raw"]["retries"] - result["controlled"]["retries"]
            
            metrics["task_specific"][task]["time_improvement"] += time_diff
            metrics["task_specific"][task]["token_reduction"] += token_diff
            metrics["task_specific"][task]["retry_reduction"] += retry_diff
            metrics["task_specific"][task]["count"] += 1
        
        # Calculate averages
        for task in metrics["task_specific"]:
            count = metrics["task_specific"][task]["count"]
            metrics["task_specific"][task]["time_improvement"] /= count
            metrics["task_specific"][task]["token_reduction"] /= count
            metrics["task_specific"][task]["retry_reduction"] /= count
        
        return metrics

    def _save_results(self, results: Dict[str, Any]):
        """Save benchmark results to file"""
        target_lang = results.get("target_language", "default")
        filename = f"benchmark_results_{results['model_key']}_{target_lang}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        with open(f"logs/{filename}", "w") as f:
            json.dump(results, f, indent=2)
            
    def get_available_models(self) -> List[str]:
        """Return list of available models from config"""
        return list(self.config.keys()) 