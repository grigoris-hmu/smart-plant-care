from flask import render_template, flash, redirect, url_for, request, session, abort, jsonify
from flask_login import login_required, current_user
#from flask_login import login_user, logout_user
from flask_babel import _
import json
from pyproj import Transformer
from . import crop
from .forms.newCropForm import newCropForm
from .models import PrefectureName, AreaName, CropTypeName, SoilTypeName, Crop, CropCoordinates
#from .models import Prefecture,Area,CropType,SoilType
from ..user.models import User
from ..sensor.models import Sensor
from .. import db
from .create_map import create_map
from .save_image import save_image
from SmartPlantCare import app
from ..sensor.models import Valve

@crop.route('/get_prefectures')
@login_required
def get_prefectures():
    lang_id = session.get('lang_id')
    prefectures = PrefectureName.query.filter_by(language_id=lang_id).order_by(PrefectureName.id.asc()).all()
    return jsonify({"prefectures": [{"id": p.prefecture_id, "name": p.name} for p in prefectures]})


@crop.route('/get_areas/<int:prefecture_id>', methods=['GET'])
@login_required
def get_areas(prefecture_id):
    lang_id = session.get('lang_id')
    areas = AreaName.query.filter_by(prefecture_id=prefecture_id,language_id=lang_id).order_by(AreaName.id.asc()).all()
    return jsonify({"areas": [{"id": a.area_id, "name": a.name} for a in areas]})


@crop.route("/crops/")
@login_required
def crops():

    ordering_by = request.args.get('ordering_by')

    ## Pagination: page value from 'page' parameter from url
    page = request.args.get('page', 1, type=int)

    if ordering_by==None:
        crops = Crop.query.order_by(Crop.id.asc()).paginate(per_page=5, page=page)
    elif ordering_by=='name':
        crops = Crop.query.order_by(Crop.name.asc()).paginate(per_page=5, page=page)
    elif ordering_by=='crop_size':
        crops = Crop.query.order_by(Crop.crop_size.desc()).paginate(per_page=5, page=page)
    else:
        return render_template('404.html'), 404
    
    return render_template("crops.html", crops=crops, ordering_by=ordering_by)


@crop.route("/new_crop/", methods=["GET", "POST"])
@login_required
def new_crop():
    
    form = newCropForm()
    lang_id = session.get('lang_id')
    crop_types = CropTypeName.query.filter_by(language_id=lang_id).order_by(CropTypeName.id.asc())
    soil_types = SoilTypeName.query.filter_by(language_id=lang_id).order_by(SoilTypeName.id.asc())

    if request.method == 'POST' and form.validate_on_submit():
        name = form.name.data
        location = form.location.data
        prefecture = form.prefecture.data
        area = form.area.data
        crop_size = form.crop_size.data
        crop_type = form.crop_type.data
        soil_type = form.soil_type.data
        coordinates_type = form.coordinates_type.data

        if form.image.data:
            try:
                image_file = save_image(app, form.image.data, 'crops_images', (640, 640))
            except:
                abort(415)
        
            crop = Crop(owner=current_user,
                        name=name,
                        location=location,
                        prefecture=prefecture,
                        area=area,
                        crop_size=crop_size,
                        crop_type=crop_type,
                        soil_type=soil_type)
        else:
            crop = Crop(owner=current_user,
                        name=name,
                        location=location,
                        prefecture=prefecture,
                        area=area,
                        crop_size=crop_size,
                        crop_type=crop_type,
                        soil_type=soil_type
                        )

        db.session.add(crop)
        db.session.commit()
        
        ### creation of its Valve.
        # Fetch the last inserted Valve to determine the next port number for our valce
        last_valve = db.session.query(Valve).order_by(Valve.id.desc()).first()

        if last_valve:
            last_port = int(last_valve.hwaddr.split(":")[-1])  # Extract last port number
        else:
            last_port = 8083  # Default starting port from here and up we play

        next_port = last_port + 1  # Increment port for new Valve

        # Create a new Valve associated with this Crop
        valve = Valve(
            crop_id=crop.id,
            status=False,  # Default status
            counter=0,  # Default counter
            hwaddr=f"ws://192.168.231.22:{next_port}"  # Assign new hwaddr with incremented port
        )

        db.session.add(valve)
        db.session.commit()

        if len(form.crop_map.data) > 0:
            try:

                coordinates = json.loads(form.crop_map.data)

                if not coordinates:
                    flash(_('ERROR: Invalid coordinates format. Expecting a list of [latitude, longitude] pairs.'), 'warning')
                else:
                    # Save coordinates (Map Data) in database
                    try:
                        
                        # Settting for tranformation from EGSA87 (EPSG:2100) to WGS84 (EPSG:4326)
                        transformer = Transformer.from_crs("epsg:2100", "epsg:4326", always_xy=False)
                            
                        for crop_coords in coordinates:
                            lon, lat = crop_coords
                            if coordinates_type == "2100":
                                lon, lat = transformer.transform(lon, lat)
                            new_coord = CropCoordinates(crop_id=crop.id, longtitute=lon, latitude=lat)
                            db.session.add(new_coord)
                        db.session.commit()
                    except Exception as e:
                        print(str(e))
                        flash(_('Error saving Crop Coordinates Data'), 'warning')
                        db.session.rollback()

            except Exception as e:
                print(str(e))
                flash(_('Error handling Crop Coordinates Data'), 'warning')
                db.session.rollback()

        flash(_('The crop <b>{name}</b> was successfully created').format(name=name), 'success')
            
        return redirect(url_for('crop.showCrop', crop_id=crop.id))

    return render_template("new_crop.html", form=form, page_title=_('Αdd new Crop'), crop_types=crop_types, soil_types=soil_types)


### User crops list ###

@crop.route("/my_crops", methods=["GET"])
@login_required
def my_crops():

    ordering_by = request.args.get('ordering_by')
    page=1
    
    user = User.query.get_or_404(1)

    if ordering_by==None:
        crops = Crop.query.filter_by(owner=current_user).order_by(Crop.id.asc()).paginate(per_page=3, page=page)
    elif ordering_by=='name':
        crops = Crop.query.filter_by(owner=current_user).order_by(Crop.name.asc()).paginate(per_page=3, page=page)
    elif ordering_by=='crop_size':
        crops = Crop.query.filter_by(owner=current_user).order_by(Crop.crop_size.desc()).paginate(per_page=3, page=page)
    else:
        return render_template('404.html'), 404

    return render_template("my_crops.html", crops=crops, owner=current_user, ordering_by=ordering_by)


@crop.route("/crop/<int:crop_id>", methods=["GET"])
def showCrop(crop_id):

    crop = Crop.query.get_or_404(crop_id)
    name = crop.name
    lang_id = session.get('lang_id')
    prefecture = PrefectureName.query.filter_by(prefecture_id=crop.prefecture, language_id=lang_id).one_or_404()
    area = AreaName.query.filter_by(area_id=crop.area, language_id=lang_id).one_or_404()
    crop_type = CropTypeName.query.filter_by(crop_type_id=crop.crop_type, language_id=lang_id).one_or_404()
    soil_type = SoilTypeName.query.filter_by(soil_type_id=crop.soil_type, language_id=lang_id).one_or_404()
    crop_coordinates = CropCoordinates.query.filter(CropCoordinates.crop_id == crop_id).order_by(CropCoordinates.id.asc()).all()
    sensors = Sensor.query.filter_by(crop_id=crop_id).order_by(Sensor.id.asc()).all()
    form = newCropForm()

    map_html = False

    if len(crop_coordinates) > 0:
        try:
            # Convert in tuple list (longitude, latitude)
            crop_coordinates_list = [(coord.longtitute, coord.latitude) for coord in crop_coordinates]
            coordinates = json.loads(json.dumps(crop_coordinates_list))

        except Exception as e:
            print(str(e))
            flash(_('Exception: Invalid coordinates format. Expecting a list of [latitude, longitude] pairs.'), 'warning')

        if coordinates:
            map_html = create_map(coordinates, "layer_name", "red", "pink", 5, name)
        else:
            flash(_('ERROR: Invalid coordinates format. Expecting a list of [latitude, longitude] pairs.'), 'warning')
 
    return render_template("crop.html", form=form, crop=crop, map_html=map_html,
                           prefecture=prefecture, area=area, crop_type=crop_type,
                            soil_type=soil_type, sensors=sensors)


@crop.route("/crops_by_owner/<int:owner_id>")
def crops_by_owner(owner_id):
    

    ordering_by = request.args.get('ordering_by')

    ## Pagination: page value from 'page' parameter from url
    page = request.args.get('page', 1, type=int)
    
    user = User.query.get_or_404(owner_id)

    if ordering_by==None:
        crops = Crop.query.filter_by(owner=user).order_by(Crop.id.asc()).paginate(per_page=3, page=page)
    elif ordering_by=='name':
        crops = Crop.query.filter_by(owner=user).order_by(Crop.name.asc()).paginate(per_page=3, page=page)
    elif ordering_by=='crop_size':
        crops = Crop.query.filter_by(owner=user).order_by(Crop.crop_size.desc()).paginate(per_page=3, page=page)
    else:
        return render_template('404.html'), 404

    return render_template("crops_by_owner.html", crops=crops, owner=user, ordering_by=ordering_by)


@crop.route("/edit_crop/<int:crop_id>", methods=['GET', 'POST'])
@login_required
def edit_crop(crop_id):

    crop = Crop.query.filter_by(id=crop_id, owner=current_user).first_or_404()
    lang_id = session.get('lang_id')
    crop_types = CropTypeName.query.filter_by(language_id=lang_id).order_by(CropTypeName.id.asc())
    soil_types = SoilTypeName.query.filter_by(language_id=lang_id).order_by(SoilTypeName.id.asc())
    crop_coordinates = CropCoordinates.query.filter(CropCoordinates.crop_id == crop_id).order_by(CropCoordinates.id.asc()).all()
    coordinates = ""

    if len(crop_coordinates) > 0:
        try:
            # Convert in tuple list (longitude, latitude)
            crop_coordinates_list = [(coord.longtitute, coord.latitude) for coord in crop_coordinates]
            coordinates = json.loads(json.dumps(crop_coordinates_list))
        except Exception as e:
            print(str(e))
            flash(_('Exception: Invalid coordinates format. Expecting a list of [latitude, longitude] pairs.'), 'warning')

    form = newCropForm(
        name = crop.name,
        location = crop.location,
        prefecture = crop.prefecture,
        area = crop.area,
        crop_size = crop.crop_size,
        crop_type = crop.crop_type,
        soil_type = crop.soil_type,
        crop_map = coordinates
        )

    if request.method == 'POST' and form.validate_on_submit():
        crop.name = form.name.data
        crop.location = form.location.data
        crop.prefecture = form.prefecture.data
        crop.area = form.area.data
        crop.crop_size = form.crop_size.data
        crop.crop_type = form.crop_type.data
        crop.soil_type = form.soil_type.data
        coordinates_type = form.coordinates_type.data

        # Map Data exists
        if len(form.crop_map.data) > 0:

            # Convert String to JSON            
            try:
                coordinates = json.loads(form.crop_map.data)

                # Settting for tranformation from EGSA87 (EPSG:2100) to WGS84 (EPSG:4326)
                transformer = Transformer.from_crs("epsg:2100", "epsg:4326", always_xy=False)
                            
                try:
                    # Delete previous Map Data
                    CropCoordinates.query.filter(CropCoordinates.crop_id == crop.id).delete()
                    #Add new Map Data
                    for crop_coords in coordinates:
                        lon, lat = crop_coords
                        if coordinates_type == "2100":
                            lon, lat = transformer.transform(lon, lat)
                        new_coord = CropCoordinates(crop_id=crop.id, longtitute=lon, latitude=lat)
                        db.session.add(new_coord)

                except Exception as e:
                    print(form.crop_map.data)
                    print(str(e))
                    flash(_('Error saving Crop Coordinates Data'), 'warning')
                    db.session.rollback()

            except Exception as e:
                print(form.crop_map.data)
                print(str(e))
                flash(_('Error handling Crop Coordinates Data'), 'warning')

        else:
            print("no map data")
            try:
                # Delete previous Map Data
                CropCoordinates.query.filter(CropCoordinates.crop_id == crop.id).delete()

            except Exception as e:
                db.session.rollback()
                print(str(e))
                flash(_('Error deleting Crop Coordinates Data'), 'warning')

        if form.image.data:
            try:
                image_file = save_image(app, form.image.data, 'crops_images', (640, 640))
            except:
                abort(415)

            crop.image = image_file

        db.session.commit()
    
        flash(_('The crop was successfully edited'), 'success')

        return redirect(url_for('crop.showCrop', crop_id=crop.id))

    return render_template("new_crop.html", form=form, crop=crop, page_title=_('Edit Crop'),
                           crop_types=crop_types,soil_types=soil_types,
                           selected_prefecture=crop.prefecture, selected_area=crop.area)


@crop.route("/delete_crop/<int:crop_id>", methods=["GET", "POST"])
@login_required
def delete_crop(crop_id):

    crop = Crop.query.filter_by(id=crop_id, owner=current_user).first_or_404()

    if crop:

        db.session.delete(crop)
        db.session.commit()

        flash(_('The crop was successfully deleted.'), 'success')

        return redirect(url_for("crop.crops"))

    flash(_('The crop was not found.'), 'warning')

    return redirect(url_for('crop.crops'), form=form)
