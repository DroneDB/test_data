<?xml version="1.0" encoding="utf-8" ?>
<ogr:FeatureCollection
     gml:id="aFeatureCollection"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://ogr.maptools.org/ test.xsd"
     xmlns:ogr="http://ogr.maptools.org/"
     xmlns:gml="http://www.opengis.net/gml/3.2">
  <gml:boundedBy><gml:Envelope srsName="urn:ogc:def:crs:EPSG::4326"><gml:lowerCorner>0 100</gml:lowerCorner><gml:upperCorner>1 105</gml:upperCorner></gml:Envelope></gml:boundedBy>
                                                                                                                                                                          
  <ogr:featureMember>
    <ogr:test gml:id="test.0">
      <gml:boundedBy><gml:Envelope srsName="urn:ogc:def:crs:EPSG::4326"><gml:lowerCorner>0.5 102.0</gml:lowerCorner><gml:upperCorner>0.5 102.0</gml:upperCorner></gml:Envelope></gml:boundedBy>
      <ogr:geometryProperty><gml:Point srsName="urn:ogc:def:crs:EPSG::4326" gml:id="test.geom.0"><gml:pos>0.5 102.0</gml:pos></gml:Point></ogr:geometryProperty>
      <ogr:prop0>value0</ogr:prop0>
    </ogr:test>
  </ogr:featureMember>
  <ogr:featureMember>
    <ogr:test gml:id="test.1">
      <gml:boundedBy><gml:Envelope srsName="urn:ogc:def:crs:EPSG::4326"><gml:lowerCorner>0 102</gml:lowerCorner><gml:upperCorner>1 105</gml:upperCorner></gml:Envelope></gml:boundedBy>
      <ogr:geometryProperty><gml:LineString srsName="urn:ogc:def:crs:EPSG::4326" gml:id="test.geom.1"><gml:posList>0 102 1 103 0 104 1 105</gml:posList></gml:LineString></ogr:geometryProperty>
      <ogr:prop0>value0</ogr:prop0>
      <ogr:prop1>0.0</ogr:prop1>
    </ogr:test>
  </ogr:featureMember>
  <ogr:featureMember>
    <ogr:test gml:id="test.2">
      <gml:boundedBy><gml:Envelope srsName="urn:ogc:def:crs:EPSG::4326"><gml:lowerCorner>0 100</gml:lowerCorner><gml:upperCorner>1 101</gml:upperCorner></gml:Envelope></gml:boundedBy>
      <ogr:geometryProperty><gml:Polygon srsName="urn:ogc:def:crs:EPSG::4326" gml:id="test.geom.2"><gml:exterior><gml:LinearRing><gml:posList>0 100 0 101 1 101 1 100 0 100</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></ogr:geometryProperty>
      <ogr:prop0>value0</ogr:prop0>
      <ogr:prop1>{ &quot;this&quot;: &quot;that&quot; }</ogr:prop1>
    </ogr:test>
  </ogr:featureMember>
</ogr:FeatureCollection>
