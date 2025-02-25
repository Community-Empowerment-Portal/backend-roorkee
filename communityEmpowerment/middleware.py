import logging
import hashlib
import json
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from redis.exceptions import RedisError
from django_redis import get_redis_connection  # Ensure django-redis is installed

# Configure logging
logger = logging.getLogger(__name__)

# List of cacheable endpoints - only include read-only, non-user-specific endpoints
CACHEABLE_ENDPOINTS = [
    "schemes/multi-state-departments",
    "states/",
    "departments/",
    "organisations/",
    "schemes/",
    "schemes/scholarship/",
    "schemes/job/",
    "criteria/",
    "procedures/",
    "documents/",
    "scheme-documents/",
    "sponsors/",
    "scheme-sponsors/",
    "choices/gender/",
    "choices/state/",
    "choices/category/"
]

CACHE_TIMEOUT = 60 * 15  # 15 minutes
# Define a common hash tag for all cache keys. This ensures they fall into the same Redis cluster slot.
COMMON_HASH_TAG = "{simplecache}"

class CacheMiddleware(MiddlewareMixin):
    def get_cache_key(self, request):
        """Generate a unique cache key based on request path and query params."""
        base_key = f"{request.path}?{request.META.get('QUERY_STRING', '')}"
        hashed_key = hashlib.md5(base_key.encode()).hexdigest()
        return f"cache:{COMMON_HASH_TAG}_{hashed_key}"

    def is_cacheable_endpoint(self, request):
        """Check if the request should be cached based on its URL."""
        return any(request.path.startswith(f"/api/{endpoint}") for endpoint in CACHEABLE_ENDPOINTS)

    def process_request(self, request):
        """Return cached response if available."""
        if request.method != "GET" or not self.is_cacheable_endpoint(request):
            return None
        
        try:
            cache_key = self.get_cache_key(request)
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {request.path}")
                cached_response = json.loads(cached_data)
                return HttpResponse(
                    cached_response["content"],
                    status=cached_response["status"],
                    content_type=cached_response["content_type"]
                )
            logger.debug(f"Cache miss for {request.path}")
        except Exception as e:
            logger.error(f"Cache error in process_request: {str(e)}")
        return None

    def process_response(self, request, response):

        """Cache successful GET responses."""
        if request.method != "GET" or response.status_code != 200 or not self.is_cacheable_endpoint(request):
            return response

        """ Invalidate cache on data modification """
        if request.method in ["POST", "PUT", "DELETE"]:
            self.invalidate_cache()

        try:
            cache_key = self.get_cache_key(request)
            # Store necessary response parts in JSON format
            cached_data = {
                "content": response.content.decode(),
                "status": response.status_code,
                "content_type": response.get("Content-Type", "text/html"),
            }
            cache.set(cache_key, json.dumps(cached_data), timeout=CACHE_TIMEOUT)
            logger.debug(f"Cached response for {request.path}")
        except Exception as e:
            logger.error(f"Cache error in process_response: {str(e)}")

        return response

    def invalidate_cache(self, path_pattern):
        """Invalidate cache for a specific API pattern using Redis SCAN."""
        try:
            redis_client = get_redis_connection("default")
            cursor = 0
            match_pattern = f"cache:{COMMON_HASH_TAG}_{hashlib.md5(path_pattern.encode()).hexdigest()}*"

            while True:
                cursor, keys = redis_client.scan(cursor=cursor, match=match_pattern)
                if keys:
                    redis_client.delete(*keys)
                    logger.debug(f"Invalidated {len(keys)} cache keys for pattern: {path_pattern}")
                if cursor == 0:
                    break

        except RedisError as e:
            logger.error(f"Redis error while invalidating cache: {e}")
        except Exception as e:
            logger.error(f"Error in invalidate_cache: {e}")
