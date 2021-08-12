from django.shortcuts import render
from django.views.generic import TemplateView
from django.shortcuts import render
from utils import params, fh_io, file_io
from django.http import HttpResponseRedirect
from django.contrib import messages
import os
import shutil

# Create your views here.

class AddUseCase(TemplateView):
    template_name = "filesystem/add_use_case.html"

    # override get method
    def get(self, request):
        return render(request, self.template_name)

    # override post method
    def post(self, request):

        # get new use case name input
        name = request.POST.get('NewUseCaseInput')
        if type(name) is str:
            name = name.lower()


        # use_case_names: use to check if user input use_case_name is already created
        records_dir = params.BASE_DIR
        use_case_names = os.listdir(records_dir)

        if name in use_case_names:
            messages.error(request, f"Use case '{name}' was already created.")
            return HttpResponseRedirect('/')

        file_hierarchy_json_path = params.file_hierarchy_json_path
        try:
            """ create json file for new use case """
            # copy ug_fence.json and than alter it.
            src = file_hierarchy_json_path / "ug.json"
            dst = file_hierarchy_json_path / f"{name}.json"
            shutil.copy(src=src, dst=dst)
            # alter json content.
            json_path = f"json_files/file_hierarchy/{name}.json"
            # change fo_use_case 'underground' to passed 'name' parameter.
            file_io.replace_value_in_json(json_path=json_path, key='fo_use_case',
                                          new_val=name, old_val="underground")
            file_io.alter_json(f_name=json_path)
            """ update the dynamic_document_values.json """
            file_io.update_dynamic_document_values(new_file_hierarchy_json_path=json_path)
            """ call create_new_fo_use_case_file function to create folder tree """
            fh_io.create_new_fo_use_case_file(json_path=json_path)

        except Exception as e:
            messages.error(request, message=e)
            return HttpResponseRedirect('/')

        messages.success(request, message=f"New use case '{name}' is successfully created.")
        return HttpResponseRedirect('/')


class AddMidasVersion(TemplateView):
    template_name = "filesystem/add_midas_version.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        new_midas_version = request.POST.get('NewMidasVersionInput') # get input

        if new_midas_version.isdigit():
            new_midas_version = "midas"+str(new_midas_version)
        elif type(new_midas_version) is str:
            new_midas_version = new_midas_version.lower()
            if 'mıdas' in new_midas_version:
                new_midas_version = new_midas_version.replace("mıdas", "midas")
            new_midas_version = new_midas_version.replace(' ','')

        try:
            fh_io.insert_new_midas_version(new_midas_version)
            messages.success(request, message="New Midas Version is Successfully Created")
            return HttpResponseRedirect('/')
        except Exception as e:
            messages.error(request, message=e)
            return HttpResponseRedirect('/')
