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

        base = os.path.abspath(os.path.dirname(__file__))
        base_dir = os.path.join(base, '../communityEmpowerment/management/commands/')
        scripts = [
            "node maharastra_scraper.js",
            "node gujarat_scraper.js",
            "node jammu_kashmir_scraper.js",
            "node meghalaya_scraper.js",
            "node puducherry_scraper.js",
            "node tamilNadu_scraper.js",
            "node up_youthWelfare.js",
            "node madhyaPradesh_scraper.js",
            "node kerela_scraper.js",
            "node manipur_scraper.js",
            "node punjab_scraper.js",
            "node andhraPradesh_scraper.js",
            "node haryana_scraper.js",
            "node assam_scraper.js",
            "node odisha_scraper.js",
            "node rajasthan_scraper.js", #PDF
            "node goa_scraper.js", #PDF,
            "node tripura_scraper.js", #PDF
            "node jharkhand_scraper.js", #PDF
            "node uttarakhand_scraper.js",
            "node sikkim_scraper.js",
            "node telangana_scraper.js",
            "node chhattisgarh_scraper.js",
            "node arunachalPradesh_scraper.js",
            "node delhi_scraper.js",
            "node ladakh_scraper.js",
            "node himachalPradesh_scraper.js"
            "node dadraAndNagarHaveli_scraper.js",
            "node nagaland_scraper.js",
            "node chandigarh_scraper.js",
            "node andamanAndNicobar_scraper.js",
            f"python {os.path.join(base_dir, '../downloadAndUploadPdfs.py')}",
            f"python {os.path.join(base_dir, '../geminiAndParsingScripts/pdfParser.py')}",
            f"python {os.path.join(base_dir, '../geminiAndParsingScripts/structureScrapedSchemes.py')}",
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
        # print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
