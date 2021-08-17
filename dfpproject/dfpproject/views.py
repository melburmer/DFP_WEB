from django.views.generic import TemplateView
from database.models import Records
from django.shortcuts import render
from django.db.models import Count

class HomePage(TemplateView):
    template_name = 'index.html'

    def get(self, request):
        target_document_keys = ["fo_use_case", "midas_version", "project",
                                "region", "record_type", "activity",
                                "soil_type", "time_of_day"]

        count = Records.objects.values('soil_type').annotate(mcount=Count('soil_type')).order_by()

        return render(request, self.template_name, {'target_document_keys':target_document_keys})
