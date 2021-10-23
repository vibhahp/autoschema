from flask import Flask, render_template, request
import os
import csv
import re
app =Flask(__name__)

@app.route('/')
def hello():
    return 'hello world'

@app.route('/index')
def home_page():
    return render_template('home.html')

@app.route('/schema', methods=['POST'])
def schema():
    #auto_schema=request.files.get('auto_csv')
    #print(auto_schema)
    # if 'file' not in request.files:
    #         print('No file part')
    #         return ''
    # file = request.files['file']
    #     # if user does not select file, browser also
    #     # submit an empty part without filename
    # if file.filename == '':
    #     print('No selected file')
    #     return ''
    #auto_schema=file.read()
    #print(auto_schema)
    
    # values=[]
    # row=0
    # #with open(auto_schema,'r') as csv_file:
    # csv_reader = csv.reader(file)
    # for line in csv_reader:
    #     row+=1
    #     values.append(line)
    # values[0][0]="columns"
    # print(values)
    schema = {"parser_settings": {
        "version": "omni.2.0",
        "file_format_type": "delimited"
    }
    }
    transform_declarations ={
        "retailer_template": {
            "custom_func": {
                "name": "lower",
                "args": [
                    {"custom_func": { "name": "external", "args": [{ "const": "retailer" }]}}
                ]
            }
        }
    }
    final_output_obj = {
            "object": {}
    }
    metaInfo = {
            "object": {
                "retailer_moniker": { "template": "retailer_template" },
                "message_source_type": { "const": "FTP_FILE" },
                "message_source": { "const": "carrier_flat_file" },
                "message_type": { "const": "CARRIER_DATA" },
                "message_source_date": {"external": "message_source_date"},
                "message_source_location": {
                    "custom_func": {
                        "name": "external",
                        "args": [{ "const": "source_filename" }]
                    }
                },
                "message_origin": { "const": "generic_file_processor" }
            }
        }
    final_output_edd_obj = {
            "object": {
                "edd_begin": {
                    "custom_func": {
                        "name": "dateTimeWithLayoutToRfc3339",
                        "args": [
                            { "xpath": "edd" },
                            { "const": "", "_comment": "input layout" },
                            {"const": "false","_comment": "input layout has timezone included or not"},
                            { "const": "", "_comment": "input timezone" },
                            { "const": "", "_comment": "output timezone" }
                        ]
                    }
                }
            }
        }
    final_output_event_obj = {
            "array": [
                {
                    "object": {
                        "date": { "template": "event_date_time" },
                        "date_raw": { "template": "event_date_time" },
                        "desc": { "xpath": "carrier_event_description" },
                        "carrier_status_code": { "template": "carrier_event_code" },
                        "event_status_code_mapping": {
                            "object": {
                                "event_code": {
                                    "custom_func": {
                                        "name": "getStatusCode",
                                        "args": [
                                            { "template": "carrier_template", "_comment": "carrier" },
                                            { "const": "",  "_comment": "service code" },
                                            { "template": "carrier_status_code_template", "_comment": "event code" },
                                            { "const": "", "_comment": "event desc" },
                                            { "const": "",  "_comment": "error code" }
                                        ]
                                    }
                                }
                            }
                        },
                        "location": {
                            "object": {
                                "city": { "xpath": "event_city" },
                                "state": { "xpath": "event_state" },
                                "zip": { "xpath": "event_zip" },
                                "country": { "xpath": "event_country_code" },
                                "lng": {"xpath": "long"},
                                "lat": {"xpath": "lat"}
                            }
                        }
                    }
                }
            ]
        }
    final_output_obj['object']['meta_info'] = metaInfo
#print(final_output_obj)

    trackingEntity = {"object": {
    "carrier": { "template": "carrier_template" },
    "retailer": { "template": "retailer_template" },
    "tracking_number": { "xpath": "" },
    "tracking_document": {
        "object": {
            "carrier_moniker": { "template": "carrier_template" },
            "retailer_moniker": { "template": "retailer_template" },
            "tracking_number": { "xpath": "" },
            }
        }
    }
    }

    file_declaration = {
    "delimiter": "",
    "data_row_index": "", # header csv
    "columns": []
    }


    f= request.files['file']
    if not os.path.isdir('static'):
        os.mkdir('static')
    filepath =os.path.join('static','auto_schema.csv')
    f.save(filepath)
    print(f.filename)
    values=[]
    row=0
    with open(filepath) as file:
        csvfile=csv.reader(file)
        for line in csvfile:
            row+=1
            values.append(line)
    values[0][0]="columns"
    print(values)
    #return 'hello'
    value_dict = {values[0][n]:[values[j][n] for j in range(1,row)] for n in range(len(values[0]))}
    if value_dict['Header Exists'][0].lower() == 'true':
        file_declaration["data_row_index"] = '2'
    else:
        file_declaration["data_row_index"] = '1'
    top=int(values[1][0])
    bottom=1
    k=[]
    dup=0
    for i in values[1][3:]:
        if i!="":
            if int(i)>top or int(i)<bottom:  
                print("\033[1;35;40m hey the given position of {0} not with in the limit\033[0;0m".format(i))
            k.append(i)
            s=set(k)
            if len(k)!=len(s):
                print("duplicates present in the positional values")

    try:
        a=value_dict['columns'][0]
        a=int(a)
    except Exception as e:
        print(e)
        print("\033[1;32;40m hey you have to give columns value as integer\033[0;0m")
    try:
        b=value_dict['Header Exists'][0].title()
        if b=="True" or b=="False":
            b=True
        b=int(b)
    except Exception as e:
        print(e)
        print("\033[1;35;40m hey you have to give Header Exists value as True or False only\033[0;0m")
        
    headers_only=["columns","Header Exists","delimiter"]
    for i,j in value_dict.items():
        if i not in headers_only and j[0]!="":
            try:
                c=j[0]
                c=int(c) 
            except Exception as e:
                print(e)
                print("\033[1;31;40m hey you have to give {0} value as integer\033[0;0m".format(i))

    #creating a dictionary with headings as keys and positions as values named as value_dict

    value_dict = {values[0][n]:[values[j][n] for j in range(1,row)] for n in range(len(values[0]))}
    if value_dict['Header Exists'][0].lower() == 'true':
        file_declaration["data_row_index"] = 2
    else:
        file_declaration["data_row_index"] = 1
    length=int(value_dict['columns'][0])
    col_len=[i for i in range(length) if i>4]
    for i in value_dict:
        if value_dict[i][0].isnumeric():
            if int(value_dict[i][0]) in col_len:
                col_len.remove(int(value_dict[i][0]))
    #value_dict.pop("statuscode")
    #value_dict['statusdescription'][1]="abcd_efg_ h" for testing 
    #for capitalize and removing special characters from statuscode
    for i in value_dict:
        if (i=='statuscode'):
            break 
    else:
        value_dict['statuscode']=[str(col_len[0]),re.sub('[^A-Za-z0-9]+', '',value_dict['statusdescription'][1].upper())]
    test_list = ['01/02/2006 3:04:05 PM','02/01/2006 3:04:05 AM','02-01-2006 3:04:05 AM','2006/01/02 3:04:05 AM','2006-01-02 3:04:05 AM','02/01/2006 3:04:05','2006-01-02T15:04:05-07:00','1585990763']
    # Handling no element found in index()
    # Using try + except + ValueError
    try :
        if value_dict['eventDateTime'][1]!="":
            test_list.index(value_dict['eventDateTime'][1])
    except ValueError as e :
        res = "Element not in list !"
        print(e)
        print("The value after catching error : " + str(res))

#adding no of columns and delimiter to the keys
    for i in range(int(value_dict['columns'][0])):
        file_declaration['columns'].append({'name':str(i)})
    file_declaration['delimiter'] = value_dict['delimiter'][0]

    #creating a dictionary for only columns except those header values like columns,header exists,delimiter
    add_values = dict(list(value_dict.items())[3:])

    #excepting the empty values which have position as null
    new_dict = dict([(value[0], key) for key, value in add_values.items() if value[0]!=""])

    #adding values to the file declaration
    for key,value in new_dict.items():
        temp = file_declaration['columns'][int(key)-1]
        temp["name"] = str(value)

    #templates for carrier and statuscode uppercase and removal of special character
    carrier_template = {
                "const": ""
            }
    carrier_status_code_template= {
        "custom_func": {
            "name": "upper",
            "args": [
            {
                "custom_func": {
                "name": "replace",
                "args": [
                    {
                    "xpath": "",
                    "_comment": "event code"
                    },
                    {
                    "const": "[[:punct:]]|\\s+",
                    "_comment": "regex exp to match"
                    },
                    {
                    "const": "",
                    "_comment": "string to replace"
                    }
                ]
                }
            }
            ]
        }
        }
    carrier_description={
                            "custom_func": {
                                "name": "getStatusCodeEx",
                                "args": [
                                    {
                                        "template": "carrier_template",
                                        "_comment": "carrier"
                                    },
                                    {
                                        "const": "",
                                        "_comment": "service code"
                                    },
                                    {
                                        "template": "carrier_status_code_template",
                                        "_comment": "event code"
                                    },
                                    {
                                        "const": "",
                                        "_comment": "event desc"
                                    },
                                    {
                                        "const": "",
                                        "_comment": "error code"
                                    },
                                    {
                                        "const": "ScanDescription",
                                        "_comment": "return parameter"
                                    }
                                ]
                            }
                        }
#adding there xpath values for templates
    carrier_template['const'] = add_values['carrier_name'][1]
    carrier_status_code_template['custom_func']['args'][0]['custom_func']['args'][0]['xpath']

    #date formats concate (date & time) and regular datetime 
    import datetime as dt
    event_date_time = {
                "custom_func": {
                    "name": "dateTimeWithLayoutToRfc3339",
                    "args": [
                        { "xpath": "", "_comment": "event date time given by carrier" },
                        { "const": "", "_comment": "input layout" },
                        { "const": "false", "_comment": "input layout has Tz(true/or false)??" },
                        { "const": "",  "_comment": "input timezone" },
                        { "const": "", "_comment": "output timezone"}
                    ]
                }
            }
    """concate_event_date_time = {
        "custom_func": {
                    "name": "dateTimeWithLayoutToRfc3339",
                    "args": [
                        {
                                "custom_func": {
                                "name": "concat",
                                "args": [
                                    { "xpath": "", "_comment": "event date" },
                                    { "const": "", "keep_leading_trailing_space": True, "_comment": "space" },
                                    { "xpath": "", "_comment": "event time" },
                                    { "const": "", "_comment": "input layout" },
                                    { "const": "false", "_comment": "input layout has Tz(true/or false)??" },
                                    { "const": "",  "_comment": "input timezone" },
                                    { "const": "", "_comment": "output timezone"}
                                ]
                                }

                        }]
    }}"""
    epooch_date_time= {
    "custom_func": {
        "name": "epochToDateTimeRfc3339",
        "args": [
        { "xpath": "", "_comment": "epoch time" },
        { "const": "SECOND", "_comment": "epoch unit" }
        ]
    }
    }
    concate_event_date_time ={
        "custom_func": {
            "name": "dateTimeWithLayoutToRfc3339",
            "args": [
            {
                "custom_func": {
                "name": "concat",
                "args": [
                    {
                    "xpath": "",
                    "_comment": "event date"
                    },
                    {
                    "xpath": "",
                    "_comment": "event time"
                    }
                ]
                },
                "_comment": "datetime"
            },
            {
                "const": "",
                "_comment": "input layout"
            },
            {
                "const": "false",
                "_comment": "input layout has timezone included or not"
            },
            {
                "const": "",
                "_comment": "input timezone"
            },
            {
                "const": "",
                "_comment": "output timezone"
            }
            ]
        }
        }
#for adding the required values to the concate date_time and regular datetime
    edd_dateTime=''
    event_dataTime = ''
    flag = ''
    try:
        if 'edd' in add_values and add_values['edd'][1]!='':
            if add_values['edd'][1] != '':
                if add_values['edd'][1][-1] == ' ':
                    add_values['edd'][1] = add_values['edd'][1][:-1]
                edd_dateTime = add_values['edd'][1]
            final_output_edd_obj["object"]["edd_begin"]["custom_func"]["args"][1]["const"] = edd_dateTime
            trackingEntity['object']['tracking_document']['object']['delivery'] = final_output_edd_obj
        if 'eventDateTime' in add_values and add_values['eventDateTime'][1]!='':
            event_dataTime = add_values['eventDateTime'][1]
            event_date_time["custom_func"]["args"][1]["const"] = event_dataTime
            
            flag = False
        elif add_values['eventtime'][1]!='' and add_values['eventdate'][1]!='':
            event_dataTime = f"{add_values['eventdate'][1]}{add_values['eventtime'][1]}"
            concate_event_date_time["custom_func"]["args"][1]['const']=event_dataTime
            flag = True
    except Exception as e :
        print(e)
        print("Please specify time in csv.")
    # print(event_date_time)
    # print("\n")
    # print(concate_event_date_time)

    #for adding the values which are given in sheet by checking they are present or not 
    for key in add_values.keys():
        if 'tracking_number' in key:
            trackingEntity['object']['tracking_number']['xpath'] = key
            trackingEntity['object']['tracking_document']['object']['tracking_number']['xpath'] = key
        if 'statuscode' in key:
            if add_values['statuscode'][0]=="":
                carrier_status_code_template['custom_func']['args'][0]['custom_func']['args'][0]['xpath']= "statusdescription"
                final_output_event_obj['array'][0]['object']['carrier_status_code']['template']="carrier_status_code_template"
            else:
                carrier_status_code_template['custom_func']['args'][0]['custom_func']['args'][0]['xpath']= key
                final_output_event_obj['array'][0]['object']['carrier_status_code']['template']="carrier_status_code_template"
        if 'statusdescription' in key:
            final_output_event_obj['array'][0]['object']['desc']['xpath']=key
        if 'eventDateTime' in key:
            event_date_time["custom_func"]["args"][0]["xpath"] = key
        
        if 'eventdate' in key:
            concate_event_date_time['custom_func']['args'][0]['custom_func']['args'][0]['xpath']=key
        if 'eventtime' in key:
            concate_event_date_time['custom_func']['args'][0]['custom_func']['args'][1]['xpath']=key
    concate_event_date_time
    if value_dict['statusdescription'][0]=="":
        del final_output_event_obj['array'][0]['object']['desc']['xpath']
        final_output_event_obj['array'][0]['object']['desc']=carrier_description
    final_output_event_obj['array'][0]['object']

    #adding all the custom functions to the major block transform declaration 
    #writing the output on json file
    import json
    schema["file_declaration"] = file_declaration
    transform_declarations["carrier_template"] = carrier_template
    transform_declarations["carrier_status_code_template"] = carrier_status_code_template
    if flag==True:
        transform_declarations["event_date_time"] = concate_event_date_time
    elif flag==False:
        transform_declarations["event_date_time"] = event_date_time
    trackingEntity['object']['tracking_document']['object']['events'] = final_output_event_obj
    final_output_obj['object']["tracking_entity"] = trackingEntity
    transform_declarations['FINAL_OUTPUT']=final_output_obj
    schema["transform_declarations"] = transform_declarations
    x=json.dumps(schema,indent=2)
    f = open("RESULT34.json",'w')
    f.write(x)
    f.close()
    print(x)

    return render_template('response.html', output_schema=x)

if __name__ =='__main__':
    app.run(debug=True)