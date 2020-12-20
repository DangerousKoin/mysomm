from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView, TemplateView, FormView, DeleteView
from .models import Winery, Wine, Grape
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from . import map_us
from .models import Wine, County
from .forms import WineryForm, WineForm, WineSearchForm, WinerySearchForm



# Create your views here.
def home(request, **kwargs):
  # If no query, then show all
  selected_wines = Wine.objects.all()
  # else show the search results

  wine_query =  []
  for county in County.objects.all():
    county_wines = selected_wines.filter(winery__county = county)
    wine_query.append({
      "name": county.name,
      "state": county.state,
      "lat": county.lat,
      "lon": county.lon,
      "count": len(county_wines)
    })
  map_data= map_us.render_map(wine_query)
  wine_search_form = WineSearchForm(auto_id='id_%s_wine')
  winery_search_form = WinerySearchForm(auto_id='id_%s_winery')
  return render(request, 'index.html', context= {
    "selected_wines": selected_wines,
    "plot": map_data,
    "wine_form": wine_search_form,
    "winery_form": winery_search_form,
    })

def profile(request):
  my_wineries = Winery.objects.filter(user=request.user.id)

  return render(request, 'profile.html', {'my_wineries': my_wineries})

def glossary(request):
  return render(request, 'glossary.html')

def about(request):
  return render(request, 'about.html')

######### WINERY ########
def find_wineries(request):
  return render(request, 'winery/index.html')

def create_winery(request):
  if request.method == 'POST':
    form = WineryForm(request.POST)
    if form.is_valid():
      input_county = form.cleaned_data['county']
      input_state = form.cleaned_data['state']
      db_county = County.objects.get(name=input_county, state=input_state)
      winery = Winery(
        name = form.cleaned_data['name'],
        address = form.cleaned_data['address'],
        region = form.cleaned_data['region'],
        county = db_county,
        city = form.cleaned_data['city'],
        zipcode = form.cleaned_data['zipcode'],
        img_url = form.cleaned_data['img_url'],
        logo_url = form.cleaned_data['logo_url'],
        user = request.user
      )
      winery.save()
      return redirect('winery_detail', winery_id=winery.id)
  form = WineryForm()
  return render(request, 'main_app/winery_form.html', {"form": form})

def winery_detail(request, winery_id):
  try:
    winery = Winery.objects.get(id=winery_id)
  except:
    return redirect('profile')
  wine_form = WineForm()
  return render(request, 'winery/detail.html', {"winery": winery, "wine_form": wine_form})

def winery_update(request, winery_id):
  ##Check to see if user owns winery, 
  ## if not redirect
  winery = Winery.objects.get(pk=winery_id)
  if request.method == 'POST':
    form = WineryForm(request.POST)
    if form.is_valid():
      input_county = form.cleaned_data['county']
      input_state = form.cleaned_data['state']
      db_county = County.objects.get(name=input_county, state=input_state)
      winery.name = form.cleaned_data['name']
      winery.address = form.cleaned_data['address']
      winery.region = form.cleaned_data['region']
      winery.county = db_county
      winery.city = form.cleaned_data['city']
      winery.zipcode = form.cleaned_data['zipcode']
      winery.img_url = form.cleaned_data['img_url']
      winery.logo_url = form.cleaned_data['logo_url']
      winery.user = request.user
      winery.save()
      return redirect('winery_detail', winery_id=winery.id)
  form = WineryForm(initial={
    'name': winery.name,
    'address': winery.address,
    'region': winery.region,
    'county': winery.county.name,
    'city': winery.city,
    'state': winery.county.state,
    'zipcode': winery.zipcode,
    'img_url': winery.img_url,
    'logo_url': winery.logo_url
    })
  return render(request, 'main_app/winery_form.html', {"form": form, "winery": winery})

class WineryDelete(DeleteView):
  model = Winery
  success_url = '/profile/'


def winery_search(request):
  if request.is_ajax() and request.method == "GET":
    filter_terms = {}
    location = {}
    for item in request.GET.items():
      if item[1] != "" and item[0] != 'csrfmiddlewaretoken':
        if item[0] == "county":
          location['county'] = item[1]
        elif item[0] == "state":
          location['state'] = item[1]
        else:
          query = item[0] + "__icontains"
          filter_terms[query] = item[1]
    if len(location) == 2:
      try:
        county = County.objects.get(name__iexact=location['county'], state__iexact=location['state'])
        filter_terms['county'] = county.id
      except:
        pass
    wineries = Winery.objects.filter(**filter_terms)[:10].values('name', 'region', 'county')
    winery_results = list(wineries)
    for winery in winery_results:
      dbcounty = County.objects.get(pk=winery['county'])
      winery['county'] = dbcounty.name
      winery['state'] = dbcounty.state
    return JsonResponse(winery_results,safe=False)
  return JsonResponse({}, status=400)

######### WINES #########
def my_wines(request):
  # wines = Wine.objects.filter(user=request.user)
  #
  # if request.wine_id:
  #   selected_wine = Wine.objects.filter(pk=request.wine_id)
  # else:
  #   selected_wine = None
  return render(request, 'wines/my_wines.html', {
    # "my_wines": wines,
    # "selected_wine": selected_wine
  })


def create_wine(request, winery_id):
  form = WineForm(request.POST)
  if form.is_valid():
    new_wine = form.save(commit=False)
    new_wine.winery_id = winery_id
    new_wine.save()
  return redirect('winery_detail', winery_id=winery_id)
  

class WineDetail(DetailView):
  model = Wine


class WineUpdate(UpdateView):
  model = Wine
  fields = ['style', 'grape', 'vintage', 'color', 'taste_notes', 'image_url', ]

class WineDelete(DeleteView):
  model = Wine
  def get_success_url(self):
    return reverse ('winery_detail', args={self.object.winery.id})

def wine_search(request):
  if request.is_ajax() and request.method == "GET":
    filter_terms = {}
    for item in request.GET.items():
      if item[1] != "" and item[0] != 'csrfmiddlewaretoken':
        if item[0] == "min_year":
          filter_terms['vintage__gte'] = item[1]
        elif item[0] == "max_year":
          filter_terms['vintage__lte'] = item[1]
        else:
          query = item[0] + "__icontains"
          filter_terms[query] = item[1]
    wines = Wine.objects.filter(**filter_terms)[:10].values('name', 'grape', 'color', 'vintage')
    wine_results = list(wines)
    colors = {}
    for c in Wine.COLOR_CHOICES:
      if c[0] != "":
        colors[c[0]] = c[1]
    for wine in wine_results:
      wine['color'] = colors[wine['color']]
    return JsonResponse(wine_results,safe=False)
  return JsonResponse({}, status=400)
  



######## GRAPES #########
def my_grapes(request):
  return render(request, 'mygrapes/index.html')


  
###### REGISTRATION ###########
def signup(request):
  error_message = ''
  if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
    form = UserCreationForm(request.POST)
    if form.is_valid():
      # This will add the user to the database
      user = form.save()
      # This is how we log a user in via code
      login(request, user)
      return redirect('about')
    else:
      error_message = 'Invalid sign up - try again'
  # A bad POST or a GET request, so render signup.html with an empty form
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)

