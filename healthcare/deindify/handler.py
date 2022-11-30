import json
def handle(req):
    di_data = {}
    raw_data = json.loads(req)
    di_data['timestamp']=raw_data['timestamp']
    di_data['device_id']=raw_data['device_id']
    di_data['patient_id']=raw_data['patient_id']
    di_data['temperature']=raw_data['temperature']
    di_data['systolic']=raw_data['systolic']
    di_data['"diastolic']=raw_data['"diastolic']
    return josn.dumps(di_data)
