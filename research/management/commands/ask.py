from django.core.management.base import BaseCommand, CommandError

from research.agent import AgentConfigError, check_setup, run_agent
from research.exporter import save_answer


class Command(BaseCommand):
    help = "Ask the research agent from the terminal: python manage.py ask \"your question\""

    def add_arguments(self, parser):
        parser.add_argument("question", nargs="+")

    def handle(self, *args, **options):
        question = " ".join(options["question"])
        try:
            check_setup()
        except AgentConfigError as exc:
            raise CommandError(str(exc)) from exc

        answer = run_agent(question, on_step=self.stdout.write)
        self.stdout.write("\n" + answer)
        for fmt, path in save_answer(question, answer).items():
            self.stdout.write(f"file saved ({fmt}): {path}")
