# Architecture

`config.py` defines the default task, allowed local model tags, sample files and iteration bounds. `agent.py` receives the CLI arguments and owns all run state. No framework schedules actions.

1. Start a fresh history with the user's original task. On each pass through the while loop, send the actor instructions and accumulated history to Ollama.
2. The client sends JSON to the loopback /api/chat endpoint with streaming disabled. JSON mode is enabled for the actor. Both roles use temperature 0, seed 42, an 8192-token context window and a 512-token output budget.
3. Parse a single JSON object. Duplicate keys, extra fields and invalid argument shapes cannot dispatch tools. Every recognized tool-shaped request is logged before checking the registry. Unparseable or ambiguous JSON receives retry feedback and is excluded from tool-request counts.
4. Run at most one registry function. Append the model response and a JSON feedback message containing a labeled result, a rejection reason or a candidate acknowledgment. Model-generated text has no execution path.
5. The evaluator receives its own system instruction, the original task and a serialized copy of the transcript. Only exact YES and NO, after trimming surrounding whitespace, are valid. The evaluator has no tool dispatcher.
6. Completion requires a YES, a final answer in this iteration, and at least one successful data call in this run. Otherwise include the verdict and retry guidance for the next actor turn. An HTTP or envelope failure stops the run with a diagnostic. The limit is configurable from 1 to 10.

## JSON actions

All arguments are required. File names are exact basenames from the allowlist. Search uses case-insensitive literal substrings. Failure counts group events by the pair of account and source. Statistics cover all rows. Each line contains time, outcome, account, source, and an optional free-text note.

```json
{"tool":"read_file","args":{"file":"sample_auth.log"}}
```
```json
{"tool":"count_failures","args":{"file":"sample_auth.log"}}
```
```json
{"tool":"search_entries","args":{"file":"sample_auth.log","query":"lab-b"}}
```
```json
{"tool":"log_stats","args":{"file":"sample_auth.log"}}
```
```json
{"final":"The report text goes here."}
```

The custom protocol requires only ordinary model text. This makes the same tool interface available to both model families. See the [Ollama chat API](https://docs.ollama.com/api/chat).

## Run record

The JSON record includes the task, model, configured limit, attempted iterations, monotonic elapsed time in seconds, tool requests with arguments and optional rejection reasons, rejection count, evaluator verdicts, status and final output. Time includes inference and tool execution, including model loading when applicable. Tool arguments and output are visible to the operator.

The statuses are completed, iteration_limit and model_error. When a run stops early, final_output holds the latest candidate if one exists, otherwise an empty string. An unfinished candidate is provisional. A model_error also includes an error field. History is in memory for one run. Only an explicit CLI record option saves the summary to disk.
