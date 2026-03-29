.PHONY: eval eval-routing eval-tools eval-quality eval-simulation eval-quiz-grounding

eval-routing:
	adk eval . tests/eval/evalsets/routing_evalset.json --config_file_path=tests/eval/eval_config_routing.json --print_detailed_results

eval-tools:
	adk eval . tests/eval/evalsets/quiz_agent_evalset.json tests/eval/evalsets/learning_content_evalset.json tests/eval/evalsets/tutor_agent_evalset.json tests/eval/evalsets/quiz_history_evalset.json tests/eval/evalsets/community_agent_evalset.json --config_file_path=tests/eval/eval_config.json --print_detailed_results

eval-quality:
	adk eval . tests/eval/evalsets/learning_content_evalset.json --config_file_path=tests/eval/eval_config_quality.json --print_detailed_results

eval-simulation:
	adk eval . tests/eval/evalsets/simulation/quiz_flow_simulation.json tests/eval/evalsets/simulation/tutor_flow_simulation.json --config_file_path=tests/eval/eval_config_simulation.json --print_detailed_results

eval-quiz-grounding:
	adk eval . tests/eval/evalsets/quiz_grounding_evalset.json --config_file_path=tests/eval/eval_config_quiz_grounding.json --print_detailed_results

eval: eval-routing eval-tools
