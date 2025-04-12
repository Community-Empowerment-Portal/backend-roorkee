import pickle
from communityEmpowerment.models import Scheme, UserInteraction
import os
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
import numpy as np
import pandas as pd
import spacy
from django.db.models import Q

def load_cosine_similarity():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cosine_sim_path = os.path.join(base_dir,'..','..', 'cosine_sim_matrix.pkl')

    with open(cosine_sim_path, 'rb') as f:
        return pickle.load(f)

def recommend_schemes(scheme_id, cosine_sim, top_n=5):
    try:
        schemes = list(Scheme.objects.all().order_by('id')) 
        scheme_ids = [s.id for s in schemes]

        if scheme_id not in scheme_ids:
            return []

        scheme_index = scheme_ids.index(scheme_id)

        top_indices = cosine_sim[scheme_index].argsort()[::-1]

        recommended_schemes = []
        count = 0
        for idx in top_indices:
            if idx != scheme_index:  # skip the same scheme
                recommended_schemes.append(schemes[idx])
                count += 1
            if count == top_n:
                break

        return recommended_schemes

    except Scheme.DoesNotExist:
        return []



def collaborative_recommendations(user_id, top_n=5, keywords=None):
    # Fetch user-scheme interactions
    interactions = UserInteraction.objects.values('user_id', 'scheme_id', 'interaction_value')
    
    if not interactions:
        return []  # Return empty if no interactions exist

    # Create a DataFrame
    df = pd.DataFrame(interactions)

    # Map user and scheme IDs to categorical indices
    user_categories = df['user_id'].astype('category')
    scheme_categories = df['scheme_id'].astype('category')
    user_ids = user_categories.cat.codes
    scheme_ids = scheme_categories.cat.codes

    # Create User-Scheme Interaction Matrix
    interaction_matrix = csr_matrix((df['interaction_value'], (user_ids, scheme_ids)))

    num_schemes = interaction_matrix.shape[1]
    n_components = min(50, num_schemes) 

    # Perform SVD
    svd = TruncatedSVD(n_components=n_components)  # Reduce dimensionality
    latent_matrix = svd.fit_transform(interaction_matrix)

    # Get the user's latent vector
    try:
        user_idx = user_categories.cat.categories.get_loc(user_id)
    except KeyError:
        return []  # Return empty if user_id is not found in the dataset

    user_vector = latent_matrix[user_idx]

    # Compute similarity scores for schemes
    scheme_latent_matrix = latent_matrix.T  # Transpose to align with schemes
    scores = scheme_latent_matrix.T.dot(user_vector)

    # Get top N recommended scheme indices
    recommended_indices = np.argsort(scores)[-top_n:][::-1]

    # Map indices back to scheme IDs
    scheme_ids = scheme_categories.cat.categories
    recommended_scheme_ids = [scheme_ids[idx] for idx in recommended_indices]

    # Fetch Scheme objects for recommendations
    recommended_schemes = list(Scheme.objects.filter(id__in=recommended_scheme_ids))
    if keywords:
        keyword_matched_schemes = Scheme.objects.filter(
            Q(tags__name__icontains=keywords) | Q(description__icontains=keywords)
        ).distinct()
        recommended_schemes = list(set(recommended_schemes) | set(keyword_matched_schemes))[:top_n]

    return recommended_schemes


nlp = spacy.load("en_core_web_sm")  # Load SpaCy's English model

def extract_keywords_from_feedback(description):
    """
    Extracts keywords from feedback descriptions using NLP.
    """
    doc = nlp(description)
    keywords = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "PROPN"]]
    return keywords
