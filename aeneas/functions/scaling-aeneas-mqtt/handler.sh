#!/bin/bash

export nano=`date +%s%N`
export OUT=/tmp/$nano.mp3
cat - > ${OUT}


a=`echo $((1 +  RANDOM % 2 ))`
export file=`echo 'p00'$a.xhtml`

curl -d $file http://${gateway}:8080/function/getobject > /tmp/$file
export filename=`date '+%M%S%s%N'`-`uuidgen -t`$nano
#export name=`echo $filename | base64`
python -m aeneas.tools.execute_task \
   ${OUT} \
   /tmp/$file \
   "task_language=eng|os_task_file_format=json|is_text_type=plain" /tmp/$filename.json  > /tmp/output.txt 
rm  ${OUT}
#rm /tmp/$file
mosquitto_pub -h ${mqttbroker} -p ${brokerport} -f /tmp/$filename.json -t tocloud -q 2
#rm /tmp/$name.json

