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
            if 'm??das' in new_midas_version:
                new_midas_version = new_midas_version.replace("m??das", "midas")
            new_midas_version = new_midas_version.replace(' ','')

        try:
            fh_io.insert_new_midas_version(new_midas_version)
            messages.success(request, message="New Midas Version is Successfully Created")
            return HttpResponseRedirect('/')
        except Exception as e:
            messages.error(request, message=e)
            return HttpResponseRedirect('/')


class AddProject(TemplateView):
    template_name = "filesystem/add_project.html"

    def get(self, request):
        # read fo use cases, they will used in form.

        fo_use_cases_to_select = file_io.read_json(params.dynamic_doc_values_path)["fo_use_case"]

        return render(request, self.template_name, {'fo_use_cases_to_select':fo_use_cases_to_select})

    def post(self, request):
        fo_use_case = request.POST.get('UseCaseSelection')
        new_project = request.POST.get('NewProjectInput')
        new_regions = request.POST.get('NewProjectRegionsInput')

        # arrange input format
        if new_regions != '' and new_regions.isdigit() is False:
            new_regions = new_regions.replace(' ', '')
            new_regions = new_regions.split(',')
            new_regions = [i for i in new_regions if i != '']  # if split list is like ['new_region','']

        try:
            fh_io.insert_new_project(fo_use_case, new_project, new_regions)
            messages.success(request, message="New Project is Successfully Created")
            return HttpResponseRedirect('/')
        except Exception as e:
            messages.error(request, message=e)
            return HttpResponseRedirect('/')



class AddRegion(TemplateView):
    template_name = "filesystem/add_region.html"


    def get(self, request):
        project_to_select = file_io.read_json(params.dynamic_doc_values_path)["project"]
        return render(request, self.template_name, {'project_to_select':project_to_select})

    def post(self, request):
        project = request.POST.get('ProjectSelection')
        new_region = request.POST.get('NewRegionInput')

        if new_region != '' and type(new_region) is not int:
            try:
                new_region = new_region.replace(' ', '')
                fh_io.insert_new_region(project, new_region)
                messages.success(request, message="New Region is successfully added to the file system.")
                return HttpResponseRedirect('/')
            except Exception as e:
                messages.error(request, message=e)
                return HttpResponseRedirect('/')
        else:
            messages.warning(request, message="Please enter a region with proper format")
            return HttpResponseRedirect('/')


class AddRecordType(TemplateView):
    template_name = "filesystem/add_record_type.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        new_record_type = request.POST.get('NewRecordTypeInput')
        if new_record_type != '' and new_record_type.isdigit() == False:
            try:
                new_record_type = new_record_type.replace(' ', '')
                fh_io.insert_new_record_type(new_record_type)
                messages.success(request, message="New record_type is successfully added to the file system.")
                return HttpResponseRedirect('/')
            except Exception as e:
                messages.error(request, message=e)
                return HttpResponseRedirect('/')

        else:
            messages.warning(request, message="Please enter a record_type with proper format")
            return HttpResponseRedirect('/')

class AddAct(TemplateView):
    template_name = "filesystem/add_act.html"

    def get(self, request):
        use_case_to_select = file_io.read_json(params.dynamic_doc_values_path)["fo_use_case"]
        return render(request, self.template_name, {'use_case_to_select':use_case_to_select})

    def post(self, request):
        fo_use_case = request.POST.get("FoUseCaseSelection")
        new_act = request.POST.get("NewActInput")

        if new_act != '' and new_act.isdigit() is False:
            try:
                new_act = new_act.replace(' ', '')
                fh_io.insert_new_activity_type(fo_use_case, new_act)
                messages.success(request, message="New act_type is successfully added to the file system.")
                return HttpResponseRedirect('/')
            except Exception as e:
                messages.error(request, message=e)
                return HttpResponseRedirect('/')
        else:
            messages.warning(request, message="Please enter a act type with proper format")
            return HttpResponseRedirect('/')
