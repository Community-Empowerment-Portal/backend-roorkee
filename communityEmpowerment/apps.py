from django.apps import AppConfig


class communityEmpowermentConfig(AppConfig):
    name = 'communityEmpowerment'
    def ready(self):
        import communityEmpowerment.signals
