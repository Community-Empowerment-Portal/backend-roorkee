from django.core.management.base import BaseCommand
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from communityEmpowerment.models import Scheme
import pickle
import re
def clean_text(text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text) 
        text = re.sub(r'\s+', ' ', text).strip()
        return text
class Command(BaseCommand):
    help = 'Precompute scheme similarity'
    


    def handle(self, *args, **kwargs):
        schemes = Scheme.objects.all()

        scheme_data = []
        for scheme in schemes:
            tags = " ".join([(" ".join([tag.name] * int(tag.weight))) for tag in scheme.tags.all()])
            description = scheme.description if scheme.description else ""
            combined = " ".join([
                scheme.title,
                scheme.funding_pattern or "",
                scheme.description or "",
                " ".join(tag.name for tag in scheme.tags.all()),
                " ".join(b.beneficiary_type for b in scheme.beneficiaries.all()),
                " ".join(s.sponsor_type for s in scheme.sponsors.all()),
                scheme.department.department_name or "",
            ])

            scheme_data.append(clean_text(combined))


        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(scheme_data)

        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

        with open('cosine_sim_matrix.pkl', 'wb') as f:
            pickle.dump(cosine_sim, f)

        self.stdout.write(self.style.SUCCESS('Successfully precomputed and saved similarity matrix!'))
