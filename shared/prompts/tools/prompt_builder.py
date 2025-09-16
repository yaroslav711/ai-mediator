"""
Prompt Builder for AI Mediator

Builds final prompts from main.md or experiments with contract schema injection.

Usage:
    # CLI
    python prompt_builder.py                    # Build from main.md
    python prompt_builder.py --experiment 001   # Build from experiment
    
    # Code
    from prompt_builder import PromptBuilder
    builder = PromptBuilder()
    prompt = builder.build()                     # From main.md
    prompt = builder.build(experiment="001")     # From experiment
"""

import json
import re
from pathlib import Path
from typing import Optional

import click


class PromptBuilder:
    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt builder.
        
        Args:
            prompts_dir: Path to prompts directory. If None, auto-detect.
        """
        if prompts_dir is None:
            # Auto-detect prompts directory
            current_file = Path(__file__).resolve()
            self.prompts_dir = current_file.parent.parent
        else:
            self.prompts_dir = prompts_dir
            
        self.contracts_dir = self.prompts_dir.parent / "contracts"
        
    def build(self, experiment: Optional[str] = None) -> str:
        """Build final prompt with contract schema injection.
        
        Args:
            experiment: Experiment number (e.g., "001"). If None, use main.md
            
        Returns:
            Complete prompt ready for LLM
        """
        # Load base prompt
        if experiment:
            prompt_file = self.prompts_dir / "experiments" / f"{experiment}_*.md"
            # Find the experiment file
            matching_files = list(self.prompts_dir.glob(f"experiments/{experiment}_*.md"))
            if not matching_files:
                raise FileNotFoundError(f"Experiment {experiment} not found")
            prompt_file = matching_files[0]
        else:
            prompt_file = self.prompts_dir / "main.md"
            
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
        prompt_content = prompt_file.read_text(encoding="utf-8")
        
        # Replace contract schema placeholders
        prompt_content = self._inject_contracts(prompt_content)
        
        return prompt_content
        
    def _inject_contracts(self, content: str) -> str:
        """Inject contract schemas into prompt content.
        
        Replaces {{CONTRACT_SCHEMA:filename.json}} with file contents.
        """
        pattern = r'\{\{CONTRACT_SCHEMA:([^}]+)\}\}'
        
        def replace_contract(match):
            filename = match.group(1)
            contract_file = self.contracts_dir / filename
            
            if not contract_file.exists():
                return f"[CONTRACT FILE NOT FOUND: {filename}]"
                
            try:
                contract_data = json.loads(contract_file.read_text(encoding="utf-8"))
                return json.dumps(contract_data, ensure_ascii=False, indent=2)
            except json.JSONDecodeError as e:
                return f"[INVALID JSON IN {filename}: {e}]"
                
        return re.sub(pattern, replace_contract, content)
        
    def list_experiments(self) -> list[str]:
        """List available experiments."""
        experiments_dir = self.prompts_dir / "experiments"
        if not experiments_dir.exists():
            return []
            
        experiments = []
        for file in experiments_dir.glob("*.md"):
            # Extract experiment number from filename (e.g., "001_fast_connect.md" -> "001")
            name = file.stem
            if "_" in name:
                exp_num = name.split("_")[0]
                experiments.append(exp_num)
                
        return sorted(experiments)


# CLI interface
@click.command()
@click.option(
    "--experiment", "-e", 
    help="Experiment number (e.g., 001). If not specified, uses main.md"
)
@click.option(
    "--output", "-o",
    help="Output file. If not specified, prints to stdout"
)
@click.option(
    "--list", "list_experiments", is_flag=True,
    help="List available experiments"
)
def main(experiment: Optional[str], output: Optional[str], list_experiments: bool):
    """Build AI Mediator prompts with contract schema injection."""
    builder = PromptBuilder()
    
    if list_experiments:
        experiments = builder.list_experiments()
        if experiments:
            click.echo("Available experiments:")
            for exp in experiments:
                click.echo(f"  {exp}")
        else:
            click.echo("No experiments found.")
        return
        
    try:
        prompt = builder.build(experiment=experiment)
        
        if output:
            Path(output).write_text(prompt, encoding="utf-8")
            click.echo(f"Prompt written to {output}")
        else:
            click.echo(prompt)
            
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        exit(1)


if __name__ == "__main__":
    main()
