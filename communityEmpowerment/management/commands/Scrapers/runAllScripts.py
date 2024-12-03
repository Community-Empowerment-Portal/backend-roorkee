import subprocess
import os
import sys
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Run all scraper scripts'

    def handle(self, *args, **kwargs):
        def run_script(script_command):
            try:
                result = subprocess.run(script_command, shell=True, check=True, capture_output=True, text=True)
                self.stdout.write(f"Output of {script_command}:\n{result.stdout}")
            except subprocess.CalledProcessError as e:
                self.stderr.write(f"Error running {script_command}:\n{e.stderr}")
                raise

        base_dir = os.path.abspath(os.path.dirname(__file__))
        scripts = [
            "node maharastra_scraper.js",
            "python maharastra_gemini.py",
            "node gujarat_scraper.js",
            "node jammu_kashmir_scraper.js",
            "node meghalaya_scraper.js",
            "node puducherry_scraper.js",
            "node tamilNadu_scraper.js",
            "node up_youthWelfare.js",
            "node madhyaPradesh_scraper.js",
            "node kerela_scraper.js",
            "node manipur_scraper.js"
            f"python {os.path.join(base_dir, '../converted_combined.py')}",
            f"python {os.path.join(base_dir, '../../../../manage.py load_data')}"
        ]

        for script in scripts:
            self.stdout.write(f"Running script: {script}")
            run_script(script)

        self.stdout.write(self.style.SUCCESS('All scripts ran successfully.'))

if __name__ == "__main__":
    try:
        Command().handle()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
