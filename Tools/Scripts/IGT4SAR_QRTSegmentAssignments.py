#-------------------------------------------------------------------------------
# Name:        QRTSegmentAssignments.py
#
# Purpose: Create Assignments from "QRT Points", "QRT Lines", "QRT Segment",
# "Air Search Patterns" or "Search Segment" feature.
#
# Author:      Don Ferguson
#
# Created:     06/25/2012
# Copyright:   (c) Don Ferguson 2012
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

# Take courage my friend help is on the way
import arcpy

# Environment variables
wrkspc=arcpy.env.workspace
arcpy.env.overwriteOutput = "True"
arcpy.env.extent = "MAXOF"

def WriteToAssignments(Areas,Area_Name,Area_Description,Ttype):
    fc3 = "Operation_Period"
    Perd=[0]
    Safety = " "
    rows1 = arcpy.SearchCursor(fc3)
    row1 = rows1.next()
    while row1:
        Perd.append(row1.Period)
        Safety = row1.Safety_Message
        row1 = rows1.next()
    OpPerid = max(Perd)
    if OpPerid==0:
        arcpy.AddMessage('No Operational Period Established - Default to 0')

    fc2="Assignments"
    rows = arcpy.InsertCursor(fc2)
    row = rows.newRow()
    row.Description = Area_Description
    row.Area_Name = Area_Name
    try:
        row.Priority = "High"
    except:
        pass

    if OpPerid>0:
        row.Period = OpPerid
        row.Safety_Note = Safety

    row.Status = "Planned"
    if Ttype=='Air':
        row.Map_Scale = 72000
    else:
        row.Map_Scale = 24000
    row.Create_Map = "Yes"
    row.Create_gpx = "Yes"
    if Area_Name in Areas:
        row.Previous_Search = "Yes"
    else:
        row.Previous_Search = "No"
    rows.insertRow(row)

    del rows
    del row

def AllPoints(Areas, SegmentName):
    arcpy.AddMessage("\nProcessing Point Assignments")
    if arcpy.Exists("QRT_Points"):
        fc1="QRT_Points"
    elif arcpy.Exists("Hasty_Points"):
        fc1 = "Hasty_Points"
    else:
        arcpy.AddError("No QRT / Hasty Points Feature Exists")

    fieldName2="UTM_Easting"
    fieldName3="UTM_Northing"

    # Get a list of areas that have already been assigned
    SName = SegmentName.split(";")
    for SegName in SName:
        Ttype='Ground'
        SegName.encode('ascii','ignore')
        where1 = ('"Area_Name" = \'{0}\''.format(SegName.replace("'","")))
        rows1 = arcpy.SearchCursor(fc1,where1)
        row1 = rows1.next()

        while row1:
            try:
                Area_Name = row1.getValue("Area_Name")
                Area_Name.encode('ascii','ignore')
                arcpy.AddMessage("QRT Points: " + Area_Name)

                PtA_X = row1.getValue(fieldName2)
                PtA_Y = row1.getValue(fieldName3)

                Descrip1 = "Search in / around " + Area_Name
                Descrip2 = " located at: " + str(int(PtA_X)) + " " + str(int(PtA_Y)) + "."

                Area_Description = Descrip1 + Descrip2

                WriteToAssignments(Areas,Area_Name, Area_Description,Ttype)

            except:
                # Get the tool error messages
                msgs = ("There was an error with {0}".format(where1))
                # Return tool error messages for use with a script tool
                #
                arcpy.AddError(msgs)
                # Print tool error messages for use in Python/PythonWin
                #
                print msgs

            row1 = rows1.next()

        del row1
        del rows1


def AllLines(Areas, SegmentName):
    arcpy.AddMessage("\nProcessing Line Assignments")
    if arcpy.Exists("QRT_Lines"):
        fc1="QRT_Lines"
    elif arcpy.Exists("Hasty_Line"):
        fc1 = "Hasty_Line"
    else:
        arcpy.AddError("No QRT / Hasty Lines Feature Exists")

    fieldName1="Length_miles"
    fieldName2="PointA_X"
    fieldName3="PointA_Y"
    fieldName4="PointB_X"
    fieldName5="PointB_Y"
    expression2 = "float(!shape.firstpoint!.split()[0])"
    expression3 = "float(!shape.firstpoint!.split()[1])"
    expression4 = "float(!shape.lastpoint!.split()[0])"
    expression5 = "float(!shape.lastpoint!.split()[1])"

    SName = SegmentName.split(";")
    for SegName in SName:
        Ttype='Ground'
        SegName.encode('ascii','ignore')
        where1 = ('"Area_Name" = \'{0}\''.format(SegName.replace("'","")))
        rows1 = arcpy.SearchCursor(fc1,where1)
        row1 = rows1.next()

        while row1:
            try:
                Area_Name = row1.getValue("Area_Name")
                Area_Name.encode('ascii','ignore')
                arcpy.AddMessage("QRT Lines: " + Area_Name)

                arcpy.CalculateField_management(fc1, fieldName1, "!SHAPE.length@miles!", "PYTHON")
                arcpy.CalculateField_management(fc1, fieldName2, expression2, "PYTHON")
                arcpy.CalculateField_management(fc1, fieldName3, expression3, "PYTHON")
                arcpy.CalculateField_management(fc1, fieldName4, expression4, "PYTHON")
                arcpy.CalculateField_management(fc1, fieldName5, expression5, "PYTHON")
                Length_miles = row1.getValue("Length_miles")
                Type = row1.getValue("Type")
                PtA_X = row1.getValue("PointA_X")
                PtA_Y = row1.getValue("PointA_Y")
                PtB_X = row1.getValue("PointB_X")
                PtB_Y = row1.getValue("PointB_Y")

                Descrip1 = "Search along " + Area_Name + " for a distance of " + str(int(Length_miles*100.0)/100.0) + " miles"
                Descrip2 = " between point 1: " + str(int(PtA_X)) + " " + str(int(PtA_Y)) + ", and point2: "
                Descrip3 = str(int(PtB_X)) + " " +str(int(PtB_Y)) + "."
                Descrip4 = "  Sweep 10 - 20 ft on each side of road/trail.  Look for decision points and location where someone may leave the trail."

                Area_Description = Descrip1 + Descrip2 + Descrip3 + Descrip4

                WriteToAssignments(Areas,Area_Name, Area_Description,Ttype)

            except:
                # Get the tool error messages
                #
                msgs = ("There was an error with {0}".format(where1))

                # Return tool error messages for use with a script tool
                #
                arcpy.AddError(msgs)
                # Print tool error messages for use in Python/PythonWin
                #
                print msgs
            row1 = rows1.next()

        del row1
        del rows1


def AllSegments(Areas, SegmentName):
    arcpy.AddMessage("\nProcessing Area (Segment) Assignments")
    fc1="Search_Segments"

    if arcpy.Exists("QRT_Segments"):
        fc4 = "QRT_Segments"
    elif arcpy.Exists("Hasty_Segments"):
        fc4 = "Hasty_Segments"
    else:
        arcpy.AddError("No QRT / Hasty Segments Feature Exists")

    fc5="AirSearchPattern"

    fieldName1="Area_Description"

    SSeg = []
    rows1 = arcpy.SearchCursor(fc1)
    row1 = rows1.next()
    while row1:
        AreaN =row1.Area_Name
        AreaN.encode('ascii','ignore')
        SSeg.append(AreaN)
        row1 = rows1.next()

    HSeg = []
    rows1 = arcpy.SearchCursor(fc4)
    row1 = rows1.next()
    while row1:
        AreaN =row1.Area_Name
        AreaN.encode('ascii','ignore')
        HSeg.append(str(AreaN))
        row1 = rows1.next()

    ASeg = []
    rows1 = arcpy.SearchCursor(fc5)
    row1 = rows1.next()
    while row1:
        AreaN =row1.Area_Name
        AreaN.encode('ascii','ignore')
        ASeg.append(str(AreaN))
        row1 = rows1.next()

    SName = SegmentName.split(";")
    for SegName in SName:
        SegName.encode('ascii','ignore')
        SgName = SegName.replace("'","")
        where1 = ('"Area_Name" = \'{0}\''.format(SgName))
        try:
            if SgName in SSeg:
                Ttype='Ground'
                rows1 = arcpy.UpdateCursor(fc1,where1)
                row1 = rows1.next()
                while row1:
                    Area_Name = row1.getValue("Area_Name")
                    Area_Name.encode('ascii','ignore')
                    arcpy.AddMessage("Search Segment: " + Area_Name)
                    Area_Description = row1.getValue(fieldName1)
                    row1.Status = "Planned"
                    rows1.updateRow(row1)
                    row1 = rows1.next()
                del row1, rows1

            elif SgName in HSeg:
                Ttype='Ground'
                rows1 = arcpy.SearchCursor(fc4,where1)
                row1 = rows1.next()
                while row1:
                    Area_Name = row1.getValue("Area_Name")
                    Area_Name.encode('ascii','ignore')
                    arcpy.AddMessage("QRT Segment: " + Area_Name)
                    Area_Description = row1.getValue(fieldName1)
                    row1 = rows1.next()
                del row1, rows1

            elif SgName in ASeg:
                Ttype='Air'
                rows1 = arcpy.SearchCursor(fc5,where1)
                row1 = rows1.next()
                while row1:
                    Area_Name = row1.getValue("Area_Name")
                    Area_Name.encode('ascii','ignore')
                    arcpy.AddMessage("Air Segment: " + Area_Name)
                    Area_Description = row1.getValue(fieldName1)
                    row1 = rows1.next()
                del row1, rows1

            ####
            WriteToAssignments(Areas,Area_Name,Area_Description,Ttype)

        except:
            # Get the tool error messages
            #
            msgs = ("There was an error with {0}".format(where1))

            # Return tool error messages for use with a script tool
            #
            arcpy.AddError(msgs)
            # Print tool error messages for use in Python/PythonWin
            #
            print msgs


########
# Main Program starts here
#######
if __name__ == '__main__':
    ## Script arguments

    PointName = arcpy.GetParameterAsText(0)  # Get the subject number

    LineName = arcpy.GetParameterAsText(1)  # Get the subject number

    SegmentName = arcpy.GetParameterAsText(2)  # Get the subject number

    fc2="Assignments"

    Areas=[]
    rows1 = arcpy.SearchCursor(fc2)
    row1 = rows1.next()
    while row1:
        AreaN =row1.Area_Name
        AreaN.encode('ascii','ignore')
        Areas.append(AreaN)
        row1 = rows1.next()

    arcpy.AddMessage("\nCreating assignments from selected areas\n")

    SegCount=0
    if PointName:
        AllPoints(Areas,PointName)
        SegCount+=1
        arcpy.AddMessage("\n")
    else:
        arcpy.AddMessage("No QRT Points Selected\n")

    if LineName:
        AllLines(Areas,LineName)
        SegCount+=1
        arcpy.AddMessage("\n")
    else:
        arcpy.AddMessage("No QRT Lines Selected\n")

    if SegmentName:
        AllSegments(Areas, SegmentName)
        SegCount+=1
        arcpy.AddMessage("\n")
    else:
        arcpy.AddMessage("No Segments Selected\n")

    if SegCount==0:
        arcpy.AddError("No Points, Lines or Segments Selected\n")

    arcpy.AddMessage("\n")