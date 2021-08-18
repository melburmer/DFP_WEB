from django.views.generic import TemplateView
from database.models import Records
from django.shortcuts import render
from django.db.models import Count
import plotly.graph_objects as go

class HomePage(TemplateView):
    template_name = 'index.html'

    def get(self, request):
        target_document_keys = ["fo_use_case", "midas_version", "project",
                                "region", "record_type", "activity",
                                "soil_type", "time_of_day"]

        total_record = Records.objects.all().count()

        return render(request, self.template_name, {'target_document_keys':target_document_keys, 'total_record':total_record})


def RenderStatGraph(request, stat_name):
    target_document_keys = ["fo_use_case", "midas_version", "project",
                            "region", "record_type", "activity",
                            "soil_type", "time_of_day"]

    stat_count = Records.objects.values(stat_name).annotate(count=Count(stat_name)).order_by()
    # handle none values
    for dictionary in stat_count:
        if dictionary[stat_name] is None:  # if none
            dictionary[stat_name] = f"undefined {stat_name}"  # make it "undefined"
    # plot pie graph
    total_count = sum([i["count"] for i in stat_count])  # get total count
    elements = [i[stat_name] for i in stat_count]  # get elements
    counts = [i["count"] for i in stat_count]  # get count

    fig = go.Figure(data=[go.Pie(labels=elements, values=counts)])
    fig.update_layout(height=500, width=700, title_text=f"<b>Pie plot for <i>{stat_name}</i></b>",paper_bgcolor="#e9ecef", font={"size":14}, title_x=0.45)
    graph = fig.to_html(full_html=False, default_height=500, default_width=700)

    return render(request, 'index.html', {'target_document_keys':target_document_keys, 'graph':graph})
