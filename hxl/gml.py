import cgi
from xml.dom import minidom

import hxl.wkt

def create_coordinates(doc, coords):
	'''Convert list of (long,lat) pairs into one space separated string'''
	coordinates = doc.createElement('gml:coordinates')

	coords_string_array = []
	for (x, y) in coords:
		coords_string_array.append('%s,%s' % (x, y))

	coords_string = ' '.join(coords_string_array)
	coordinates.appendChild(doc.createTextNode(coords_string))

	return coordinates

def add_multipolygon(doc, geom, name, polygons):
	multiPolygon = doc.createElement('gml:MultiPolygon')
	multiPolygon.setAttribute('srsName', 'http://www.opengis.net/gml/srs/epsg.xml#4326')

	for polygon in polygons:
		coordinates = create_coordinates(doc, polygon.coords)
	
		linearRing = doc.createElement('gml:LinearRing')
		linearRing.appendChild(coordinates)
	
		outerBoundaryIs = doc.createElement('gml:outerBoundaryIs')
		outerBoundaryIs.appendChild(linearRing)
	
		polygon = doc.createElement('gml:Polygon')
		polygon.appendChild(outerBoundaryIs)
	
		polygonMember = doc.createElement('gml:polygonMember')
		polygonMember.appendChild(polygon)

		multiPolygon.appendChild(polygonMember)

	geom.appendChild(multiPolygon)

def add_points(doc, geom, wkts):
	multiPoint = doc.createElement('gml:MultiPoint')
	multiPoint.setAttribute('srsName', 'http://www.opengis.net/gml/srs/epsg.xml#4326')

	for (name, point) in wkts:
		#It's the caller's responsibility to check that all the points given
		#are actually points
		assert type(point) is hxl.wkt.Point

		coordinates = create_coordinates(doc, [point.coord])

		point = doc.createElement('gml:Point')
		point.appendChild(coordinates)

		pointMember = doc.createElement('gml:pointMember')
		pointMember.appendChild(point)
		multiPoint.appendChild(pointMember)

	geom.appendChild(multiPoint)

def create_gml_header(layer_name):
	'''Create a generic WFS transaction to insert geometry into a layer.'''

	doc = minidom.Document()

	escaped_layer_name = cgi.escape(layer_name)

	wfs = doc.createElement('wfs:Transaction')
	wfs.setAttribute('service', 'WFS')
	wfs.setAttribute('version', '1.0.0')
	wfs.setAttribute('xmlns:wfs', 'http://www.opengis.net/wfs')
	wfs.setAttribute('xmlns:topp', 'http://www.openplans.org/topp')
	wfs.setAttribute('xmlns:gml', 'http://www.opengis.net/gml')
	wfs.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')

	#FIXME: I think(?) we need to pass the URL of the 'topp' schema which is on the geoserver we
	#are connecting to
	wfs.setAttribute('xmlns:schemaLocation', 'http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.0.0/WFS-transaction.xsd http://www.openplans.org/topp http://localhost:8080/geoserver/wfs/DescribeFeatureType?typename=topp:%s' % (escaped_layer_name,))

	country = doc.createElement('topp:%s' % (escaped_layer_name,))

	geom = doc.createElement('topp:the_geom')
	country.appendChild(geom)

	insert = doc.createElement('wfs:Insert')
	insert.appendChild(country)

	wfs.appendChild(insert)
	doc.appendChild(wfs)

	return (doc, geom)

def insert_multi_polygon_gml(layer_name, name, polygons):
	'''Create a WFS transaction to insert a polygon into a layer'''

	(doc, geom) = create_gml_header(layer_name)
	add_multipolygon(doc, geom, name, polygons)

	return doc

def insert_multi_point_gml(layer_name, wkts):
	'''Create a WFS transaction to insert points into a layer'''

	(doc, geom) = create_gml_header(layer_name)
	add_points(doc, geom, wkts)

	return doc

__all__ = ['insert_multi_polygon_gml', 'insert_multi_point_gml']
