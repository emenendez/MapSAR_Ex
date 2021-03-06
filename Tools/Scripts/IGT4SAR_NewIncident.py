#-------------------------------------------------------------------------------
# Name:       NewIncident.py
# Purpose: Create a new Incident for IGT4SAR and Project in the correct
#  coordinate system.
#
# Author:      Don Ferguson
#
# Created:     02/18/2013
# Copyright:   (c) Don Ferguson 2013
# Licence:
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  The GNU General Public License can be found at
#  <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

#!/usr/bin/env python
import arcpy, os
import shutil, errno
import traceback
import sys
from arcpy import env
arcpy.env.overwriteOutput = True

def copyanything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise


########
# Main Program starts here
#######

#in_fc  - Source Folder
in_fc = "C:\MapSAR_Ex\Template"
# Set date and time vars
timestamp = ''
now = datetime.datetime.now()
todaydate = now.strftime("%m_%d")
todaytime = now.strftime("%H_%M_%p")
timestamp = '{0}_{1}'.format(todaydate,todaytime)

arcpy.AddMessage("\n")

#out_fc  - Target Folder
out_fc = arcpy.GetParameterAsText(0)
if out_fc == '#' or not out_fc:
    arcpy.AddMessage("You need to provide a valid out_fc")

#Set the spatial reference
output_coordinate_system = arcpy.GetParameterAsText(1)
if output_coordinate_system == '#' or not output_coordinate_system:
    arcpy.AddMessage("You need to provide a valid Coordinate System")

#Set the transformation
transformation = arcpy.GetParameterAsText(2)

# Get initial operational information: Subject Name, Incidnet Name, Incident
# Number and Lead Agency
SubName = arcpy.GetParameterAsText(3)
if SubName == '#' or not SubName:
    arcpy.AddMessage("No Subject information provided.  It can be entered at a later time.\n")

IncidName = arcpy.GetParameterAsText(4)
if IncidName == '#' or not IncidName:
    arcpy.AddMessage("No Incident Name provided. It can be entered at a later time.\n")

IncidNum = arcpy.GetParameterAsText(5)
if IncidNum == '#' or not IncidNum:
    arcpy.AddMessage("No Incident Number provided. It can be entered at a later time.\n")

LeadAgency = arcpy.GetParameterAsText(6)
if LeadAgency == '#' or not LeadAgency:
    arcpy.AddMessage("No Lead Agency information provided. It can be entered at a later time.\n")

if (output_coordinate_system != "") and (output_coordinate_system != "#"):
    sr = output_coordinate_system

##
##srp=arcpy.SpatialReference()
##srp.loadFromString(output_coordinate_system)
##arcpy.AddMessage(srp.datumName)

copyanything(in_fc, out_fc)

# Set environment settings
templ= os.path.join(in_fc,'SAR_Default.gdb')
wrkspc = os.path.join(out_fc,'SAR_Default.gdb')
env.workspace = wrkspc

# Set local variables
#arcpy.RefreshCatalog(wrkspc)
datasetList = arcpy.ListDatasets()

spatial_ref = arcpy.Describe("Base_Data").spatialReference

try:
    for fclist in datasetList:
        # Execute GetCount and if some features have been selected, then
        #  execute DeleteFeatures to remove the selected features.
#        arcpy.AddMessage(fclist)
        arcpy.Delete_management(fclist)

except Exception as e:
    # If an error occurred, print line number and error message
    tb = sys.exc_info()[2]
    print("Line {0}".format(tb.tb_lineno))
    print(e.message)

##arcpy.RefreshCatalog(wrkspc)
arcpy.AddMessage("Projecting feature datasets to the desired coordinate system")
try:
    for fclist in datasetList:
        # Execute GetCount and if some features have been selected, then
        #  execute DeleteFeatures to remove the selected features.
        arcpy.AddMessage(fclist)        # Determine the new output feature class path and name
        outData = os.path.join(wrkspc, fclist)
        inData = os.path.join(templ, fclist)
        arcpy.Project_management(inData, outData, sr, transformation)

except Exception as e:
    # If an error occurred, print line number and error message
    tb = sys.exc_info()[2]
    print("Line {0}".format(tb.tb_lineno))
    print(e.message)
    arcpy.AddMessage("Unable to create a new incident due to problems with Projection")
    sys.exit()

arcpy.Compact_management(templ)
arcpy.Compact_management(wrkspc)

mxd_nA = os.path.join(out_fc,'IncidentNo.mxd')
mxd = arcpy.mapping.MapDocument(mxd_nA)

df = arcpy.mapping.ListDataFrames(mxd)[0]
df.spatialReference = sr
if IncidName:
    df.name = IncidName # Set the name of the main dataframe to the Incident Name

# Add the SARToolBox
# arcpy.AddToolbox("C:\\MapSAR_Ex\\Tools\\SAR_Toolbox100.tbx")

mxd.save()

if IncidNum:
    mxd_nB = os.path.join(out_fc, (IncidNum.replace(" ","") + '.mxd'))
    arcpy.AddMessage('Save map as {0}'.format(mxd_nB))
    mxd.saveACopy(mxd_nB)
    del mxd
    del df
    os.remove(mxd_nA)
    mxd = arcpy.mapping.MapDocument(mxd_nB)
    df = arcpy.mapping.ListDataFrames(mxd)[0]


if SubName:
    SubjectInfo = os.path.join(wrkspc,"Subject_Information")
    cursor = arcpy.UpdateCursor(SubjectInfo)
    for row in cursor:
        row.setValue('Name', SubName)
        cursor.updateRow(row)
    arcpy.AddMessage("update Subject Information domain")
    arcpy.TableToDomain_management(SubjectInfo, "Subject_Number", "Name", wrkspc, "Subject_Number", "Subject_Number", "REPLACE")
    try:
        arcpy.SortCodedValueDomain_management(wrkspc, "Subject_Number", "DESCRIPTION", "ASCENDING")
    except:
        pass
else:
    arcpy.AddMessage("You have not provided a valid Subject Name")

if LeadAgency:
    LeadInfo =os.path.join(wrkspc,"Lead_Agency")
    cursor = arcpy.UpdateCursor(LeadInfo)
    for row in cursor:
        row.setValue('Lead_Agency', LeadAgency)
        cursor.updateRow(row)
    arcpy.AddMessage("update Lead Agency domain")
    arcpy.TableToDomain_management(LeadInfo, "Lead_Agency", "Lead_Agency", wrkspc, "Lead_Agency", "Lead_Agency", "REPLACE")
    try:
        arcpy.SortCodedValueDomain_management(wrkspc, "Lead_Agency", "DESCRIPTION", "ASCENDING")
    except:
        pass
else:
    arcpy.AddMessage("You have not provided a valid Lead Agency")

dfSpatial_Ref = df.spatialReference.name
dfSpatial_Type = df.spatialReference.type
arcpy.AddMessage("\nThe Coordinate System for the dataframe is: " + dfSpatial_Type)
dfSpatial_Type = df.spatialReference.type
arcpy.AddMessage("The Datum for the dataframe is: " + dfSpatial_Ref)
if dfSpatial_Type=='Projected':
    arcpy.AddMessage("Be sure to turn on USNG Grid in Data Frame Properties.")
arcpy.AddMessage("\n")

## Update Incident Information if it is provided by user
if IncidName and IncidNum:
    IncidInfo =os.path.join(wrkspc,"Incident_Info")
    cursor = arcpy.UpdateCursor(IncidInfo)
    for row in cursor:
        row.setValue('Incident_Name', IncidName)
        row.setValue('Incident_Number', IncidNum)
        row.setValue('Lead_Agency', LeadAgency)
        row.setValue("MapDatum", dfSpatial_Ref)
        cursor.updateRow(row)

    arcpy.AddMessage("update Incident Information domain")
    arcpy.TableToDomain_management(IncidInfo, "Incident_Name", "Incident_Name", wrkspc, "Incident_Name", "Incident_Name", "REPLACE")
    try:
        arcpy.SortCodedValueDomain_management(wrkspc, "Incident_Name", "DESCRIPTION", "ASCENDING")
    except:
        pass

    ## Update Opertion Period Information
    OpInfo = os.path.join(wrkspc,"Operation_Period")
    cursor = arcpy.UpdateCursor(OpInfo)
    for row in cursor:
        row.setValue('Period', 1)
        cursor.updateRow(row)
    # Update Operational Period Information
    arcpy.AddMessage("update Operation Period domain")

    fieldnames = [f.name for f in arcpy.ListFields(OpInfo)]
    if "Period_Text" in fieldnames:
        pass
    else:
         arcpy.AddField_management(OpInfo,"Period_Text", "TEXT")

    arcpy.CalculateField_management(OpInfo, "Period_Text", "!Period!", "PYTHON_9.3", "")
    arcpy.TableToDomain_management(OpInfo, "Period", "Period_Text", wrkspc, "Period", "Period_Text", "REPLACE")
    try:
        arcpy.SortCodedValueDomain_management(wrkspc, "Period", "DESCRIPTION", "ASCENDING")
    except:
        pass


del dfSpatial_Ref, dfSpatial_Type

del mxd