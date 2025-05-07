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
            f"node {os.path.join(base_dir, '../Scrapers/maharastra_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/gujarat_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/jammu_kashmir_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/meghalaya_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/puducherry_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/tamilNadu_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/up_youthWelfare.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/madhyaPradesh_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/kerala_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/manipur_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/punjab_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/andhraPradesh_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/haryana_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/assam_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/odisha_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/rajasthan_scraper.js')}",  # PDF
            f"node {os.path.join(base_dir, '../Scrapers/goa_scraper.js')}",  # PDF
            f"node {os.path.join(base_dir, '../Scrapers/tripura_scraper.js')}",  # PDF
            f"node {os.path.join(base_dir, '../Scrapers/jharkhand_scraper.js')}",  # PDF
            f"node {os.path.join(base_dir, '../Scrapers/uttarakhand_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/sikkim_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/telangana_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/chhattisgarh_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/arunachalPradesh_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/delhi_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/ladakh_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/himachalPradesh_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/dadraAndNagarHaveli_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/nagaland_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/chandigarh_scraper.js')}",
            f"node {os.path.join(base_dir, '../Scrapers/andamanAndNicobar_scraper.js')}",
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
