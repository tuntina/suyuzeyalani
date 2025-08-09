import io
import sys
import json
import ee

from flask import Flask, render_template, request, flash
import geemap.foliumap as geemap
from branca.element import Element

# Earth Engine için StringIO yönlendirmesi
sys.modules['StringIO'] = io

app = Flask(__name__)
app.secret_key = 'secret'

# Earth Engine initialize
try:
    ee.Initialize(project='even-sun-457317-v8')
except Exception:
    ee.Authenticate()
    ee.Initialize(project='even-sun-457317-v8')


def otsu_threshold(image, feature):
    band = image.bandNames().get(0).getInfo()
    stats = image.reduceRegion(
        ee.Reducer.histogram(255), feature, 30, bestEffort=True
    ).getInfo().get(band, {})
    counts = stats.get('histogram', [])
    means  = stats.get('bucketMeans', [])
    if not counts or not means:
        return 0
    total    = sum(counts)
    sum_mean = sum(c * m for c, m in zip(counts, means))
    best_var = 0
    thresh   = means[0]
    w0 = sum0 = 0
    for c, m in zip(counts, means):
        w0 += c
        if w0 == 0 or w0 == total:
            continue
        sum0 += c * m
        m0   = sum0 / w0
        w1   = total - w0
        m1   = (sum_mean - sum0) / w1
        var_between = w0 * w1 * (m0 - m1) ** 2
        if var_between > best_var:
            best_var = var_between
            thresh   = m
    return thresh


def fetch_s1_mask(polar, start, end, feature):
    coll = (
        ee.ImageCollection('COPERNICUS/S1_GRD')
          .filterBounds(feature)
          .filterDate(start, end)
          .filter(ee.Filter.listContains('transmitterReceiverPolarisation', polar))
          .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
          .select(polar)
    )
    if coll.size().getInfo() == 0:
        return None
    img    = coll.median()
    thresh = otsu_threshold(img.select(polar), feature)
    return img.lt(thresh).selfMask().clip(feature)


def fetch_s2_mask(method, start, end, feature):
    coll = (
        ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
          .filterBounds(feature)
          .filterDate(start, end)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
    )
    if coll.size().getInfo() == 0:
        return None
    img = coll.median()
    idx = (
        img.normalizedDifference(['B3', 'B8'])
        if method == 'NDWI'
        else img.normalizedDifference(['B3', 'B11'])
    )
    thresh = otsu_threshold(idx, feature)
    return idx.gt(thresh).selfMask().clip(feature)


@app.route('/', methods=['GET', 'POST'])
def index():
    m = geemap.Map(
        center=[38, 35],
        zoom=6,
    )

    area_vals   = [None, None, None]
    label_texts = [None, None]
    masks       = [None, None]
    colors      = ['blue', 'yellow']

    satellites = [
        request.form.get('satellite1', 'Sentinel-1'),
        request.form.get('satellite2', 'Sentinel-1')
    ]
    methods_ = [
        request.form.get('method1', ''),
        request.form.get('method2', '')
    ]
    years = [
        request.form.get('year1', ''),
        request.form.get('year2', '')
    ]
    months = [
        request.form.get('month1', ''),
        request.form.get('month2', '')
    ]

    if request.method == 'POST':
        drawn = request.form.get('drawn_geojson')
        if not drawn:
            flash('Lütfen önce bir poligon çizin.')
        else:
            geom    = json.loads(drawn)
            ee_geom = ee.Geometry(geom)
            fc      = ee.FeatureCollection([ee.Feature(ee_geom)])

            # Alan katmanı
            m.addLayer(
                fc.style(color='red', fillColor='00000000'),
                {}, 'Poligon'
            )

            # İki görüntü için maske ve alan
            for i in [1, 2]:
                sat    = satellites[i-1]
                method = methods_[i-1]
                year   = years[i-1]
                month  = months[i-1]
                if not all([sat, method, year, month]):
                    continue

                label_texts[i-1] = f"{sat} {method} {year}-{int(month):02d}"
                start = f"{year}-{int(month):02d}-01"
                end_m = (int(month) % 12) + 1
                end_y = int(year) + (1 if int(month) == 12 else 0)
                end   = f"{end_y}-{end_m:02d}-01"

                mask = (
                    fetch_s1_mask(method, start, end, fc)
                    if sat == 'Sentinel-1'
                    else fetch_s2_mask(method, start, end, fc)
                )
                masks[i-1] = mask
                if mask:
                    area_m2 = (
                        ee.Image.pixelArea()
                          .updateMask(mask)
                          .reduceRegion(ee.Reducer.sum(), fc, 30)
                          .get('area')
                          .getInfo()
                        or 0
                    )
                    area_vals[i-1] = round(area_m2 / 1e6, 2)
                    m.addLayer(
                        mask,
                        {'palette': [colors[i-1]], 'opacity': 0.5},
                        label_texts[i-1]
                    )


            # Manuel legend
            legend_dict = {}
            if label_texts[0]:
                legend_dict[label_texts[0]] = colors[0]
            if label_texts[1]:
                legend_dict[label_texts[1]] = colors[1]
            if masks[0] and masks[1]:
                legend_dict['Kesişim'] = 'purple'

            legend_html = '<div style="position:fixed;bottom:50px;right:50px;'
            legend_html += 'background:white;padding:10px;border:2px solid grey;'
            legend_html += 'border-radius:6px;z-index:9999;"><strong>Lejant</strong>'
            legend_html += '<ul style="list-style:none;padding:0;margin:5px 0 0 0;">'
            for label, color in legend_dict.items():
                legend_html += (
                    f'<li style="margin-bottom:4px;">'
                    f'<span style="display:inline-block;width:12px;'
                    f'height:12px;background:{color};margin-right:6px;"></span>'
                    f'{label}</li>'
                )
            legend_html += '</ul></div>'
            m.get_root().html.add_child(Element(legend_html))

    map_html = m.to_html()
    return render_template(
        'index.html',
        map_html=map_html,
        area_vals=area_vals,
        label_texts=label_texts,
        satellites=satellites,
        methods=methods_,
        years=years,
        months=months
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
