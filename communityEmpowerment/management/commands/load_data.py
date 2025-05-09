import json
import os
from django.core.management.base import BaseCommand
from communityEmpowerment.models import State, Department, Resource,Organisation, Scheme, Beneficiary, Document, Sponsor, SchemeBeneficiary, SchemeDocument, SchemeSponsor, Criteria, Procedure,Tag, Benefit
from urllib.parse import urlparse

class Command(BaseCommand):
    help = 'Load data from JSON file into database'

    def handle(self, *args, **kwargs):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(base_dir, '../scrapedData/combined_schemes_data.json')
        with open(file_path, 'r') as file:
            data = json.load(file)
            self.load_data(data)
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded data into database'))

    def truncate(self, value, max_length=200):
        if value and isinstance(value, str):
            return value[:max_length]
        return value
    
    def truncateDescription(self, value):
        if value and isinstance(value, str):
            return value
        return value

    def load_data(self, data):
        state_resources = {}
        for state_data in data['states']:
            state_name = self.truncate(state_data['state_name']).strip().title()
            state, created = State.objects.get_or_create(
                state_name=state_name
            )

            for department_data in state_data['departments']:
                department_name = self.truncate(department_data['department_name'])
                department, created = Department.objects.get_or_create(
                    state=state,
                    department_name=department_name
                )

                for organisation_data in department_data['organisations']:
                    organisation_name = self.truncate(organisation_data['organisation_name'])
                    organisation, created = Organisation.objects.get_or_create(
                        department=department,
                        organisation_name=organisation_name
                    )

                    for scheme_data in organisation_data['schemes']:
                        title = self.truncate(scheme_data['title'])
                        description = self.truncateDescription(scheme_data.get('description'))
                        scheme_link = self.truncate(scheme_data.get('scheme_link'))
                        funding_pattern = self.truncate(scheme_data.get('funding_pattern', 'State'))
                        pdf_url = self.truncate(scheme_data.get('pdf_url'))
                        scheme, created = Scheme.objects.get_or_create(
                            title=title,
                            department=department,
                            defaults={
                                'introduced_on': scheme_data.get('introduced_on'),
                                'valid_upto': scheme_data.get('valid_upto'),
                                'funding_pattern': funding_pattern,
                                'description': description,
                                'scheme_link': scheme_link,
                                'pdf_url': pdf_url
                            }
                        )
                        if not created:
                            scheme.introduced_on = scheme_data.get('introduced_on')
                            scheme.valid_upto = scheme_data.get('valid_upto')
                            scheme.funding_pattern = funding_pattern
                            scheme.description = description
                            scheme.scheme_link = scheme_link
                            scheme.pdf_url = pdf_url
                            scheme.save()

                        parsed_url = urlparse(scheme_link)
                        if parsed_url.scheme and parsed_url.netloc:
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            if state.id not in state_resources:
                                state_resources[state.id] = set()
                            state_resources[state.id].add(base_url)


                        for beneficiary_data in scheme_data['beneficiaries']:
                            beneficiary_type = self.truncate(beneficiary_data)
                            if beneficiary_type is not None:
                                beneficiary, created = Beneficiary.objects.get_or_create(
                                    beneficiary_type=beneficiary_type
                                )
                                SchemeBeneficiary.objects.get_or_create(
                                    scheme=scheme,
                                    beneficiary=beneficiary
                                )

                        for document_data in scheme_data['documents']:
                            if not document_data:
                                continue
                            document_name = self.truncate(document_data)
                            document, created = Document.objects.update_or_create(
                                document_name=document_name
                                # defaults={'requirements': requirements}
                            )
                            SchemeDocument.objects.get_or_create(
                                scheme=scheme,
                                document=document
                            )


                        for sponsor_data in scheme_data['sponsors']:
                            sponsor_type = self.truncate(sponsor_data)
                            sponsor, created = Sponsor.objects.get_or_create(
                                sponsor_type=sponsor_type
                            )
                            SchemeSponsor.objects.get_or_create(
                                scheme=scheme,
                                sponsor=sponsor
                            )
                            
                        for criteria_data in scheme_data['criteria']:
                            description = self.truncate(criteria_data)

                            criteria, created = Criteria.objects.update_or_create(
                                scheme=scheme,
                                description=description,
                                defaults={
                                    'value': None,
                                    'criteria_data': description
                                }
                            )

                        for procedure_data in scheme_data['procedures']:
                            step_description = self.truncate(procedure_data)
                            Procedure.objects.update_or_create(
                                scheme=scheme,
                                step_description=step_description
                            )
                        if 'benefits' in scheme_data:
                            
                            for benefit_data in scheme_data['benefits']:
                                benefit_type = self.truncateDescription(benefit_data.get('benefit_type'))
                                if benefit_type:
                                    benefit, created = Benefit.objects.get_or_create(
                                        benefit_type=benefit_type
                                    )
                                    scheme.benefits.add(benefit)

                        if scheme_data["tags"] is not None:
                            for tag_name in scheme_data['tags']:
                                
                                tag_name = self.truncate(tag_name)
                                tag, created = Tag.objects.get_or_create(name=tag_name)
                                scheme.tags.add(tag)
        

        for state_id, base_urls in state_resources.items():
            state = State.objects.get(id=state_id)
            for base_url in base_urls:
                Resource.objects.get_or_create(
                    state_name=state,
                    resource_link=base_url
                )


                    
                        
