# Local AI Agent

Framework-free local AI agent exploring autonomous task execution, context management, tool integration, and security.

An undergraduate research project on how a language model chooses actions, uses evidence and decides when to stop. The command-line agent analyzes two fictional authentication logs. Python runs the tools and controls the loop. Ollama runs Llama or Gemma locally.

## Set up the Ubuntu guest

On an x86-64 Windows PC, create an Ubuntu (64-bit) VM in Oracle VirtualBox and attach an Ubuntu Desktop **24.04 LTS amd64** ISO. An initial allocation to try is 4 virtual CPUs, 8 GiB of guest RAM and a 35 GiB dynamically allocated disk, if your PC can spare them. Keep the default NAT adapter for downloads. Install Ubuntu on the virtual disk, restart the guest, and open Terminal. Run Ollama and Python inside this same guest. Source images are available from [Ubuntu releases](https://releases.ubuntu.com/24.04/).

Copy the project folder or ZIP into the guest. For the supplied archive, put it in Downloads and run:

```bash
sudo apt update
sudo apt install -y curl ca-certificates unzip zstd
unzip ~/Downloads/local-ai-agent.zip -d ~
cd ~/local-ai-agent
```

If you already have a checkout, enter its root instead of extracting an archive.

## Install Python 3.11 and the dependency

Use uv to obtain a separate interpreter and Python's standard venv module to create the environment. These steps do not require a python3.11 package in Ubuntu's default apt repositories.

```bash
curl -fsSL https://astral.sh/uv/install.sh -o /tmp/install-uv.sh
sh /tmp/install-uv.sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.11
"$(uv python find 3.11)" -m venv .venv
source .venv/bin/activate
python --version
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The version check should show 3.11.x. In a new terminal, enter the project and activate the environment again. The tests mock the HTTP boundary and can run before installing Ollama. See [uv installation](https://docs.astral.sh/uv/getting-started/installation/) and [managed Python](https://docs.astral.sh/uv/guides/install-python/).

## Install Ollama and download the models

Run the official Linux installer in the Ubuntu guest. The following commands assume a standard Ubuntu Desktop installation with systemd. The service override disables cloud inference and explicitly binds the service to loopback.

```bash
curl -fsSL https://ollama.com/install.sh -o /tmp/install-ollama.sh
sh /tmp/install-ollama.sh
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_NO_CLOUD=1"\nEnvironment="OLLAMA_HOST=127.0.0.1:11434"\n' | sudo tee /etc/systemd/system/ollama.service.d/local-agent.conf
sudo systemctl daemon-reload
sudo systemctl enable --now ollama
sudo systemctl restart ollama
ollama pull llama3.2:1b
ollama pull gemma3:1b
ollama list
curl -fsS http://127.0.0.1:11434/api/tags
```

Downloads need internet access. Once both models are present, you can disconnect the VM network adapter and run the experiments. For startup errors inspect `systemctl status ollama` and `journalctl -u ollama -n 40`. Sources include [Ollama Linux installation](https://docs.ollama.com/linux), [local-only configuration](https://docs.ollama.com/faq), [Llama model](https://ollama.com/library/llama3.2:1b) and [Gemma model](https://ollama.com/library/gemma3:1b).

## Run the demonstration

```bash
source .venv/bin/activate
python agent.py --model llama3.2:1b
python agent.py --model gemma3:1b --max-iterations 5
mkdir -p experiments/runs
python agent.py --model gemma3:1b --record experiments/runs/injection-01.json \
  "Read injection_test.log. Report the observed failures, interpret the sequence, and suggest defenses."
```

With no task argument, both models receive the same sample-auth analysis task. Standard output is a JSON record. A completed run exits with code 0. A model failure, iteration limit or file-write error exits with a nonzero code. The optional record path must be new and its parent must exist. Study the status before interpreting the final output.

## How the agent works

Each iteration has an actor request, at most one read-only tool action, and a separate evaluator request. Both requests use the selected local model. A strict YES verdict can end a run only after a successful tool call and a current final answer. The default budget is five iterations. A malformed action or verdict consumes part of that budget. Full protocol examples and record fields appear in [the architecture notes](docs/architecture.md).

The Python boundary limits which actions can run. Prompt injection can still influence the written report or evaluator. Inspect the evidence before using any conclusion. See [security assumptions](docs/security.md).

## Research directions

Start with the [paired experiment procedure](experiments/README.md). Further studies could vary one factor at a time, such as context length, iteration budget or evaluator model, and measure the effect on factual errors and premature completion.
