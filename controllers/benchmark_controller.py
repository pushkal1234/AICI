import time
from datetime import datetime
from typing import Dict, Any, List
from langchain.llms import Ollama
import tiktoken
import json

class BenchmarkController:
    def __init__(self):
        self.results = []
        
    def _generate_raw_response(self, text: str, task_type: str, model: str) -> tuple:
        """Generate response without controller"""
        start_time = time.time()
        retries = 0
        
        try:
            llm = Ollama(model=model, temperature=0)
            
            # Basic prompt based on task
            prompts = {
                "translation": "Translate this to German: ",
                "sql": "Generate SQL query for the {text} and the response should only contain sql query",
                "json": "Convert this text to JSON: ",
                "sentiment": "List sentiment of each sentence in the given text in JSON format only: {positive:count, negative:count, neutral:count}" 
            }
            
            response = llm.invoke(f"{prompts[task_type]}{text}")
            
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
                "retries": retries
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "time_taken": time.time() - start_time,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "retries": retries
            }

    def _generate_controlled_response(self, text: str, task_type: str, model: str, controller) -> dict:
        """Generate response with controller"""
        start_time = time.time()
        
        try:
            if task_type == "translation":
                input_data = {"text": text, "target_language": "german"}
                response, tokens = controller.generate_translation(input_data)
            elif task_type == "sql":
                input_data = {"text": text}
                response, tokens = controller.generate_sql_query(input_data)
            elif task_type == "json":
                # Add required fields for JSON processing
                input_data = {
                    "text": text,
                    "date": datetime.now().strftime("%Y-%m-%d"),
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
                response, tokens = controller.generate_sentiment(text)
            
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
                "retries": len(controller.total_output_list) - 1 if hasattr(controller, 'total_output_list') else 0
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "time_taken": time.time() - start_time,
                "time_unit": "seconds",
                "tokens": {"input": 0, "output": 0, "total": 0},
                "retries": 0
            }

    def run_benchmark(self, test_cases: List[Dict[str, Any]], model: str = "phi3") -> Dict[str, Any]:
        """Run benchmarks for both controlled and raw approaches"""
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "results": []
        }
        
        for test in test_cases:
            result = {
                "task_type": test["type"],
                "input": test["text"],
                "raw": self._generate_raw_response(test["text"], test["type"], model),
                "controlled": self._generate_controlled_response(
                    test["text"], 
                    test["type"], 
                    model,
                    test["controller"]
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
        filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"logs/{filename}", "w") as f:
            json.dump(results, f, indent=2) 