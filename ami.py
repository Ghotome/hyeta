# -*- coding: utf-8 -*-

import datetime
import json
import os
import re
import sys
import telnetlib

import requests

import settings

telnet_session = telnetlib.Telnet(settings.connection['address'], settings.connection['port'])
username = "Username: " + settings.login_data['username']
secret = "Secret: " + settings.login_data['secret']
telnet_session.write("Action:login".encode('ascii') + b"\n"
                     + username.encode('ascii') + b"\n"
                     + secret.encode('ascii') + b"\n\n")

current_string = ''
result = {}
incoming_calls = {}
outgoing_calls = {}
timestamp_outgoing_answered = ''
timestamp_answer = ''
variables = {}
client_number = {}
item_dict = {}
subscriber_name = {}
start_timestamp = {}
connected_line = {}
end_timestamp = {}
event_timestamp = {}
event_name = {}
dial_status = {}
operator = {}
record_name = {}
record = {}
file_id = {}
payload = {}
all_logs = {}
file = {}
duration = {}
duration_result = {}
count = {}
login = {}
lid = {}

while True:
    event_string = ''
    elements_string = ''
    read_some = telnet_session.read_some()
    string = read_some.decode('utf8', 'replace').replace('\r\n', '#')

    if not string.endswith('##'):
        current_string = current_string + string

    if string.endswith('##'):
        current_string = current_string + string
        current_string = current_string.replace('##', '$')
        current_string = current_string.replace('\n', '#')
        current_string = current_string.replace('\r', '#')
        current_string = current_string.replace('"', '')
        current_string = current_string.replace('\\', '')

        events = re.findall(r'[A-Z][\w]+:\s[^$]+', current_string)
        for event in events:
            event_elements = re.findall(r'[A-Z][\w]+:\s[^#]+', event)

            for element in event_elements:
                element = '"' + element.replace(': ', '": "') + '\", '
                elements_string += element
            event_string += '"result": ' + '{' + elements_string + '}'
            event_string = event_string.replace('}{', '},{')
            event_string = event_string.replace(', }', '}, ')
        event_string = '{' + event_string + '}'
        event_string = event_string.replace('}, }', '}}')

        try:

            result = json.loads(event_string)
            if settings.DEBUG:
                print(str(datetime.datetime.now().strftime("%Y-%m-%d %M:%S -- "))
                      + "DEBUG: CURRENT LINE -- " + str(result['result']))
            else:
                continue
            if 'Linkedid' in result['result']:
                if (result['result']['Linkedid'] in all_logs) is False:
                    all_logs[result['result']['Linkedid']] = str(result['result']) + "\n\n"
                elif "'Exten': 'h'" in str(result['result']) and \
                        (result['result']['Linkedid'] in all_logs) is True:
                    if result['result']['Linkedid'] in all_logs:
                        file[result['result']['Linkedid']] = open('/home/fishhead/asterisk/all_logs/'
                                                                  + result['result']['Linkedid'], 'a')
                        all_logs[result['result']['Linkedid']] += str(result['result']) + "\n\n"
                        file[result['result']['Linkedid']].write(str(all_logs[result['result']['Linkedid']]))
                        file[result['result']['Linkedid']].close()
                else:
                    all_logs[result['result']['Linkedid']] += str(result['result']) + "\n\n"

            # INCOMING CALLS

            if ('MixMonitorStart' in result['result'].values() and
                'check-abon' in result['result'].values()) is True:

                if (result['result']['Linkedid'] in outgoing_calls and
                    result['result']['Linkedid'] in incoming_calls) is False:

                    start_timestamp[result['result']['Linkedid']] = int(str(result['result']['Timestamp']) \
                                                                        .split('.')[0])

                    timestamp_answer = datetime.datetime.fromtimestamp(float(result['result']['Timestamp'])) \
                        .strftime("%M:%S")

                    if str(result['result']['CallerIDNum']).startswith('+'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum'][3:]
                    elif str(result['result']['CallerIDNum']).startswith('3'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum'][2:]
                    elif str(result['result']['CallerIDNum']).startswith('0'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum']
                    else:
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum']

                    if '<unknown>' in result['result']['CallerIDName']:
                        lid[result['result']['Linkedid']] = settings.get_elma_lid_id(
                            str(client_number[result['result']['Linkedid']]))
                        if lid[result['result']['Linkedid']] == '':
                            subscriber_name[result['result']['Linkedid']] = "[Найти]" \
                                                                            + "(" \
                                                                            + settings.elma_settings[
                                                                                'lid_search'] \
                                                                            + client_number[
                                                                                result['result']['Linkedid']] \
                                                                            + '"%7D' \
                                                                            + ")" + "  " \
                                                                                    "" \
                                                                            + 'или [создать]' + "(" \
                                                                            + settings.elma_settings[
                                                                                'lid_create'] + ") лид"
                        else:
                            subscriber_name[result['result']['Linkedid']] = '[Лид: ' + \
                                                                            lid[result['result']['Linkedid']][1] + ']' \
                                                                            + "(" + settings.elma_settings['lid_link'] \
                                                                            + lid[result['result']['Linkedid']][0] \
                                                                            + "))"
                    else:
                        login[result['result']['Linkedid']] = str(client_number[result['result']['Linkedid']])
                        login[result['result']['Linkedid']] = settings.get_abills_uid(
                            str(login[result['result']['Linkedid']]))
                        subscriber_name[result['result']['Linkedid']] = '[Абонент: ' \
                                                                        + str(login[result['result']['Linkedid']][0]) \
                                                                        + ", " \
                                                                        + str(login[result['result']['Linkedid']][1]) \
                                                                        + ']' \
                                                                        + '(' + settings.abills_settings[
                                                                            'abon_link'] + str(
                            login[result['result']['Linkedid']][2]) + ')'
                        lid[result['result']['Linkedid']] = settings.get_elma_lid_id(
                            str(client_number[result['result']['Linkedid']]))
                        if lid[result['result']['Linkedid']] == '':
                            lid[result['result']['Linkedid']] = ''
                        else:
                            lid[result['result']['Linkedid']] = [lid[result['result']['Linkedid']][0]]

                    incoming_calls[result['result']['Linkedid']] = "/event/" \
                                                                   + "Поступил новый звонок" \
                                                                   + " ///DELIMITER/// " \
                                                                   + "/status/" \
                                                                   + "Звонок начат" \
                                                                   + " ///DELIMITER/// " \
                                                                   + "/time/" \
                                                                   + "00:00" \
                                                                   + " ///DELIMITER/// "

                    if settings.DEBUG:
                        print(str(datetime.datetime.now().strftime(
                            "%Y-%m-%d %M:%S -- ")) + "DEBUG: INCOMING CALL STARTED WITH VALUES: \nCLIENT NUM: "
                              + client_number[result['result']['Linkedid']])
                    else:
                        continue

            if ('Hangup' in result['result'].values()) is True and \
                    ('BUSY' in result['result'].values()) is False \
                    and result['result']['Linkedid'] in incoming_calls:

                end_timestamp[result['result']['Linkedid']] = int(str(result['result']['Timestamp']) \
                                                                  .split('.')[0])
                employers = settings.get_employers_list()
                if settings.DEBUG:
                    print(str(datetime.datetime.now().strftime(
                        "%Y-%m-%d %M:%S -- ")) + "DEBUG: EMPLOYERS LIST: " + str(employers))
                else:
                    continue

                cdr_result = settings.get_cdr_records(result['result']['Linkedid'])

                for records in cdr_result:

                    # GET STATUS
                    if records['status'] == 'BUSY':
                        dial_status[result['result']['Linkedid']] = 'Оператор занят'
                    elif records['status'] == 'NO ANSWER':
                        dial_status[result['result']['Linkedid']] = 'Оператор не отвечает'
                    elif records['status'] == 'ANSWERED':
                        dial_status['status'] = 'Отвечен'
                    elif records['status'] == 'FAILED':
                        dial_status['status'] = 'Ошибка во время звонка'
                    else:
                        dial_status['status'] = 'Неизвестный статус'

                    # GET EVENT
                    if records['lastapp'] != 'Hangup':
                        if records['lastapp'] == 'Queue':
                            event_name[result['result']['Linkedid']] = 'Звонок оператору - ' \
                                                                       + str(records['dstchannel']) \
                                                                           .split('/')[1] \
                                                                           .split('-')[0]
                        else:
                            event_name[result['result']['Linkedid']] = 'Неизвестное событие'

                    # GET EVENT DURATION
                    if records['latency'] != 0:
                        event_timestamp[result['result']['Linkedid']] = str(records['latency'])
                    else:
                        event_timestamp[result['result']['Linkedid']] = '0'

                    incoming_calls[result['result']['Linkedid']] += "/event/" \
                                                                    + event_name[result['result']['Linkedid']] \
                                                                    + " ///DELIMITER/// " \
                                                                    + "/status/" \
                                                                    + dial_status[result['result']['Linkedid']] \
                                                                    + " ///DELIMITER/// " \
                                                                    + "/time/" \
                                                                    + event_timestamp[result['result']['Linkedid']] \
                                                                    + " ///DELIMITER/// "
                    if settings.DEBUG:
                        print(str(datetime.datetime.now().strftime(
                            "%Y-%m-%d %M:%S -- ")) + "DEBUG: CURRENT EVENT -- " + str(record))
                    else:
                        continue

                incoming_calls[result['result']['Linkedid']] += "/event/" + "Звонок завершён" \
                                                                + " ///DELIMITER/// " \
                                                                + "/status/" \
                                                                + "Звонок завершён" \
                                                                + " ///DELIMITER/// " \
                                                                + "/time/" \
                                                                + str(datetime.datetime \
                                                                      .fromtimestamp(end_timestamp[
                                                                                         result[
                                                                                             'result'][
                                                                                             'Linkedid']]
                                                                                     -
                                                                                     start_timestamp[
                                                                                         result[
                                                                                             'result'][
                                                                                             'Linkedid']])
                                                                      .strftime("%M:%S"))

                rows_split = incoming_calls[result['result']['Linkedid']].split(' ///DELIMITER/// ')
                rows = []

                for item in rows_split:
                    if '/event/' in item:
                        item_dict[result['result']['Linkedid']] = {"event": '', "status": '', "time": ''}
                        item_dict[result['result']['Linkedid']]['event'] = item.replace('/event/', '').replace(
                            '{', '').replace('}', '').replace('"', '').replace("'", '')

                    elif '/status/' in item:
                        item_dict[result['result']['Linkedid']]['status'] = item.replace('/status/', '')

                    elif '/time/' in item:
                        item_dict[result['result']['Linkedid']]['time'] = item.replace('/time/', '')
                        rows.append(item_dict[result['result']['Linkedid']])

                os.system('ls /home/fishhead/asterisk/records/ >> /dev/null')
                if result['result']['Linkedid'] in record_name:
                    if ("Разговор" in str(incoming_calls[result['result']['Linkedid']])) is True:
                        if os.path.isfile('/home/fishhead/asterisk/records/' +
                                          str(record_name[result['result']['Linkedid']])):
                            record[result['result']['Linkedid']] = {"file": open(
                                '/home/fishhead/asterisk/records/' + str(
                                    record_name[result['result']['Linkedid']]),
                                'rb')}

                            api_upload_file = requests.post(settings.elma_settings['link']
                                                            + 'pub/v1/disk/directory/'
                                                            + settings.elma_settings[
                                                                'directory_id'] + '/upload',
                                                            files=record[result['result']['Linkedid']],
                                                            headers={
                                                                'X-Token': settings.elma_settings['token'],
                                                            })

                            file_id[result['result']['Linkedid']] = json.loads(api_upload_file.content)['file'][
                                '__id']
                            if settings.DEBUG:
                                print(str(datetime.datetime.now().strftime(
                                    "%Y-%m-%d %M:%S -- ")) + "DEBUG: FILE CREATE -- " + str(
                                    api_upload_file.content))
                            else:
                                continue
                        else:
                            file_id[result['result']['Linkedid']] = 'NONE'
                            if settings.DEBUG:
                                print(str(datetime.datetime.now().strftime(
                                    "%Y-%m-%d %M:%S -- ")) + "DEBUG: RECORD FILE NOT FOUND")
                            else:
                                continue
                    else:
                        file_id[result['result']['Linkedid']] = 'MISSED'
                        if settings.DEBUG:
                            print(str(datetime.datetime.now().strftime(
                                "%Y-%m-%d %M:%S -- ")) + "DEBUG: MISSED CALL, NO FILE UPLOADS NEEDED")
                        else:
                            continue

                if result['result']['Linkedid'] in lid:
                    if lid[result['result']['Linkedid']] != '':
                        if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                and ('MISSED' in file_id[result['result']['Linkedid']]) is False:

                            payload[result['result']['Linkedid']] = {"context": {
                                "status_zvonka": [{"code": "otvechen", "name": "📥Отвечен"}],
                                "type": [{"code": "vkhodyashii", "name": "Входящий"}],
                                "__name": str(client_number[result['result']['Linkedid']]),
                                "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                "poslednii_operator": operator[result['result']['Linkedid']][1],
                                "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                "record": [file_id[result['result']['Linkedid']]],
                                "svyazannye_lidy": [lid[result['result']['Linkedid']][0]],
                                "call_logs":
                                    {
                                        "rows": rows
                                    }
                            }
                            }
                        else:
                            payload[result['result']['Linkedid']] = {"context": {
                                "status_zvonka": [{"code": "ne_otvechen", "name": "🔻Не отвечен"}],
                                "type": [{"code": "vkhodyashii", "name": "Входящий"}],
                                "__name": str(client_number[result['result']['Linkedid']]),
                                "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                "poslednii_operator": operator[result['result']['Linkedid']][1],
                                "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                "svyazannye_lidy": [lid[result['result']['Linkedid']][0]],
                                "call_logs":
                                    {
                                        "   rows": rows
                                    }
                            }
                            }
                    else:
                        if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                and ('MISSED' in file_id[result['result']['Linkedid']]) is False:

                            payload[result['result']['Linkedid']] = {"context": {
                                "status_zvonka": [{"code": "otvechen", "name": "📥Отвечен"}],
                                "type": [{"code": "vkhodyashii", "name": "Входящий"}],
                                "__name": str(client_number[result['result']['Linkedid']]),
                                "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                "poslednii_operator": operator[result['result']['Linkedid']][1],
                                "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                "record": [file_id[result['result']['Linkedid']]],
                                "call_logs":
                                    {
                                        "rows": rows
                                    }
                            }
                            }
                        else:
                            payload[result['result']['Linkedid']] = {"context": {
                                "status_zvonka": [{"code": "ne_otvechen", "name": "🔻Не отвечен"}],
                                "type": [{"code": "vkhodyashii", "name": "Входящий"}],
                                "__name": str(client_number[result['result']['Linkedid']]),
                                "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                "poslednii_operator": operator[result['result']['Linkedid']][1],
                                "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                "call_logs":
                                    {
                                        "rows": rows
                                    }
                            }
                            }

                api_create_object = requests.post(settings.elma_settings['link'] + 'pub/v1/app/'
                                                  + settings.elma_settings['namespace'] + '/'
                                                  + settings.elma_settings['incoming_calls'] + '/create',
                                                  data=json.dumps(payload[result['result']['Linkedid']]),
                                                  headers={
                                                      'X-Token': settings.elma_settings['token'],
                                                  })

                incoming_calls.pop(result['result']['Linkedid'], None)
                client_number.pop(result['result']['Linkedid'], None)
                connected_line.pop(result['result']['Linkedid'], None)
                end_timestamp.pop(result['result']['Linkedid'], None)
                start_timestamp.pop(result['result']['Linkedid'], None)
                event_timestamp.pop(result['result']['Linkedid'], None)
                variables.pop(result['result']['Linkedid'], None)
                item_dict.pop(result['result']['Linkedid'], None)
                subscriber_name.pop(result['result']['Linkedid'], None)
                start_timestamp.pop(result['result']['Linkedid'], None)
                connected_line.pop(result['result']['Linkedid'], None)
                end_timestamp.pop(result['result']['Linkedid'], None)
                event_timestamp.pop(result['result']['Linkedid'], None)
                event_name.pop(result['result']['Linkedid'], None)
                dial_status.pop(result['result']['Linkedid'], None)
                file_id.pop(result['result']['Linkedid'], None)
                record.pop(result['result']['Linkedid'], None)
                record_name.pop(result['result']['Linkedid'], None)
                payload.pop(result['result']['Linkedid'], None)
                login.pop(result['result']['Linkedid'], None)
                lid.pop(result['result']['Linkedid'], None)
                file_id.pop(result['result']['Linkedid'], None)

                if settings.DEBUG:
                    print(str(datetime.datetime.now().strftime(
                        "%Y-%m-%d %M:%S -- ")) + "DEBUG: API RESPONSE -- " + str(
                        api_create_object.content.decode('utf-8')))
                else:
                    continue

            # OUTGOING CALLS

            if ('Linkedid' in result['result'] and
                '202' not in result['result']['CallerIDNum']) is True:

                if (result['result']['Linkedid'] in incoming_calls) is False and \
                        (result['result']['Linkedid'] in outgoing_calls) is False:
                    if 'DialBegin' in result['result']['Event'] and 'callout' in result['result'].values() and \
                            result['result']['ChannelState'] == '4':
                        if 'DialString' in result['result']:
                            start_timestamp[result['result']['Linkedid']] = int(
                                str(result['result']['Timestamp']).split('.')[0])
                            client_number[result['result']['Linkedid']] = \
                                str(result['result']['DialString']).split('@')[0]
                            outgoing_calls[result['result']['Linkedid']] = "/event/" \
                                                                           + "Звонок на номер " \
                                                                           + client_number[result['result']['Linkedid']] \
                                                                           + " ///DELIMITER/// " \
                                                                           + "/status/" \
                                                                           + "Звонок начался" \
                                                                           + " ///DELIMITER/// " \
                                                                           + "/time/" + "00:00" \
                                                                           + " ///DELIMITER/// "

                            record_name[result['result']['Linkedid']] = datetime.datetime.now().strftime(
                                "%Y-%m-%d-%H:%M") \
                                                                        + "-" \
                                                                        + str(result['result']['CallerIDNum']) + "-" \
                                                                        + str(
                                client_number[result['result']['Linkedid']]) \
                                                                        + '.wav'
                            if settings.DEBUG:
                                print(str(datetime.datetime.now().strftime("%Y-%m-%d %M:%S -- "))
                                      + 'DEBUG: OUTGOING CALL STARTED WITH VALUES: \nCLIENT NUM: '
                                      + client_number[result['result']['Linkedid']] + "\nRECORD NAME: "
                                      + record_name[result['result']['Linkedid']])

                if (result['result']['Linkedid'] in outgoing_calls) is True \
                        and (result['result']['Linkedid'] in incoming_calls) is False:

                    if ('DialBegin' in result['result']['Event']) is False:

                        if result['result']['Exten'] != 'h' and \
                                ('Hangup' in str(result['result'].values())) is False and \
                                ('QueueMemberStatus' in result['result'].values()) is False:

                            timestamp_outgoing_events = datetime.datetime.fromtimestamp(
                                float(result['result']['Timestamp'])) \
                                .strftime("%H:%M:%S")
                            event_timestamp[result['result']['Linkedid']] = datetime.datetime.fromtimestamp(
                                int(str(result['result']['Timestamp'].split('.')[0])) -
                                start_timestamp[result['result']['Linkedid']]).strftime("%M:%S")

                            if 'DialState' in result['result']['Event']:
                                event_name[result['result']['Linkedid']] = 'Попытка звонка на номер ' \
                                                                           + client_number[result['result']['Linkedid']]
                                if result['result']['ChannelStateDesc'] == 'PROGRESS':
                                    dial_status[result['result']['Linkedid']] = 'Ожидание соединения'
                                elif result['result']['ChannelStateDesc'] == 'CONGESTION':
                                    dial_status[result['result']['Linkedid']] = 'Ожидание соединения'
                                else:
                                    dial_status[result['result']['Linkedid']] = 'Ожидание соединения'
                            elif 'BridgeEnter' in result['result']['Event'] and result['result']['Priority']:
                                event_name[result['result']['Linkedid']] = 'Разговор с абонентом ' \
                                                                           + client_number[result['result']['Linkedid']]
                                dial_status[result['result']['Linkedid']] = 'Звонок в процессе'
                            elif 'MusicOnHoldStart' in result['result']['Event']:
                                event_name[result['result']['Linkedid']] = 'Звонок переведён'
                                dial_status[result['result']['Linkedid']] = 'Звонок на удержании'
                            else:
                                event_name[result['result']['Linkedid']] = 'Попытка звонка на номер ' \
                                                                           + client_number[result['result']['Linkedid']]
                                dial_status[result['result']['Linkedid']] = 'Ожидание соединения'
                                if settings.DEBUG:
                                    print(str(datetime.datetime.now().strftime(
                                        "%Y-%m-%d %M:%S -- ")) + "DEBUG: UNKNOWN STATUS >> DEFAULT USED: " + str(
                                        result))
                                else:
                                    continue

                            outgoing_calls[result['result']['Linkedid']] += "/event/" \
                                                                            + str(
                                event_name[result['result']['Linkedid']]) \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/status/" \
                                                                            + dial_status[result['result']['Linkedid']] \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/time/" \
                                                                            + event_timestamp[
                                                                                result['result']['Linkedid']] \
                                                                            + " ///DELIMITER/// "
                        else:

                            timestamp_outgoing_finished = datetime.datetime.fromtimestamp(
                                float(result['result']['Timestamp'])) \
                                .strftime("%H:%M:%S")
                            end_timestamp[result['result']['Linkedid']] = datetime.datetime.fromtimestamp(
                                int(str(result['result']['Timestamp']).split('.')[0]) -
                                start_timestamp[result['result']['Linkedid']]).strftime("%M:%S")

                            outgoing_calls[result['result']['Linkedid']] += "/event/" + "Звонок завершён" \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/status/" + "Конец звонка" \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/time/" \
                                                                            + end_timestamp[
                                                                                result['result']['Linkedid']]

                            employers = settings.get_employers_list()
                            if settings.DEBUG:
                                print(str(datetime.datetime.now().strftime(
                                    "%Y-%m-%d %M:%S -- ")) + "DEBUG: EMPLOYERS LIST: " + str(employers))
                            else:
                                continue

                            if len(str(result['result']['CallerIDNum'])) <= 3 or \
                                    len(str(result['result']['ConnectedLineNum'])) <= 3:
                                for number in employers:
                                    if str(number['number']) == str(result['result']['CallerIDNum']):
                                        operator[result['result']['Linkedid']] = [result['result']['CallerIDNum'],
                                                                                  number['name']]
                                        break
                                    if str(number['number']) == str(result['result']['ConnectedLineNum']):
                                        operator[result['result']['Linkedid']] = [result['result']['ConnectedLineNum'],
                                                                                  number['name']]
                                        break
                                    else:
                                        operator[result['result']['Linkedid']] = \
                                            [result['result']['CallerIDNum'], ['74b8577e-d453-4b2b-898a-bc01055c2e58'],
                                             'DEFAULT!']

                                if settings.DEBUG:
                                    print(str(datetime.datetime.now().strftime(
                                        "%Y-%m-%d %M:%S -- ")) + "DEBUG: OPERATOR: " + str(
                                        operator[result['result']['Linkedid']]))
                                else:
                                    continue

                                login[result['result']['Linkedid']] = str(client_number[result['result']['Linkedid']])
                                login[result['result']['Linkedid']] = settings.get_abills_uid(
                                    str(login[result['result']['Linkedid']]))

                                if ('NONE' in str(login[result['result']['Linkedid']])) is True:
                                    lid[result['result']['Linkedid']] = settings.get_elma_lid_id(
                                        str(client_number[result['result']['Linkedid']]))
                                    if lid[result['result']['Linkedid']] == '':
                                        subscriber_name[result['result']['Linkedid']] = "[Найти]" \
                                                                                        + "(" \
                                                                                        + settings.elma_settings[
                                                                                            'lid_search'] \
                                                                                        + client_number[
                                                                                            result['result'][
                                                                                                'Linkedid']] \
                                                                                        + '"%7D' \
                                                                                        + ")" + "  " \
                                                                                                "" \
                                                                                        + 'или [создать]' + "(" \
                                                                                        + settings.elma_settings[
                                                                                            'lid_create'] + ") лид"
                                    else:
                                        subscriber_name[result['result']['Linkedid']] = '[Лид: ' + \
                                                                                        lid[result['result'][
                                                                                            'Linkedid']][
                                                                                            1] + ']' \
                                                                                        + "(" + settings.elma_settings[
                                                                                            'lid_link'] \
                                                                                        + lid[result['result'][
                                            'Linkedid']][0] \
                                                                                        + "))"
                                else:
                                    subscriber_name[result['result']['Linkedid']] = '[Абонент: ' \
                                                                                    + str(
                                        login[result['result']['Linkedid']][0]) \
                                                                                    + ", " \
                                                                                    + str(
                                        login[result['result']['Linkedid']][1]) \
                                                                                    + ']' \
                                                                                    + '(' + settings.abills_settings[
                                                                                        'abon_link'] + str(
                                        login[result['result']['Linkedid']][2]) + ')'
                                    lid[result['result']['Linkedid']] = settings.get_elma_lid_id(
                                        str(client_number[result['result']['Linkedid']]))
                                    if lid[result['result']['Linkedid']] == '':
                                        lid[result['result']['Linkedid']] = ''
                                    else:
                                        lid[result['result']['Linkedid']] = [lid[result['result']['Linkedid']][0]]

                            rows_split = outgoing_calls[result['result']['Linkedid']].split(' ///DELIMITER/// ')
                            rows = []

                            for item in rows_split:
                                if '/event/' in item:
                                    item_dict[result['result']['Linkedid']] = {"event": '', "status": '', "time": ''}
                                    item_dict[result['result']['Linkedid']]['event'] = item.replace('/event/', '') \
                                        .replace('{', '') \
                                        .replace('}', '') \
                                        .replace('"', '') \
                                        .replace("'", '')

                                elif '/status/' in item:
                                    item_dict[result['result']['Linkedid']]['status'] = item.replace('/status/', '')

                                elif '/time/' in item:
                                    item_dict[result['result']['Linkedid']]['time'] = item.replace('/time/', '')
                                    rows.append(item_dict[result['result']['Linkedid']])

                            os.system('ls /home/fishhead/asterisk/records/ >> /dev/null')
                            if result['result']['Linkedid'] in record_name:
                                if 'Разговор' in outgoing_calls[result['result']['Linkedid']]:
                                    if os.path.isfile('/home/fishhead/asterisk/records/' + str(
                                            record_name[result['result']['Linkedid']])):
                                        record[result['result']['Linkedid']] = {"file": open(
                                            '/home/fishhead/asterisk/records/' + str(
                                                record_name[result['result']['Linkedid']]),
                                            'rb')}

                                        api_upload_file = requests.post(settings.elma_settings['link']
                                                                        + 'pub/v1/disk/directory/'
                                                                        + settings.elma_settings[
                                                                            'directory_id'] + '/upload',
                                                                        files=record[result['result']['Linkedid']],
                                                                        headers={
                                                                            'X-Token': settings.elma_settings['token'],
                                                                        })

                                        file_id[result['result']['Linkedid']] = \
                                            json.loads(api_upload_file.content)['file'][
                                                '__id']

                                        if settings.DEBUG:
                                            print(str(datetime.datetime.now().strftime(
                                                "%Y-%m-%d %M:%S -- ")) + "DEBUG: FILE CREATE -- " + str(
                                                api_upload_file.content))
                                        else:
                                            continue
                                    else:
                                        file_id[result['result']['Linkedid']] = 'NONE'
                                        if settings.DEBUG:
                                            print(str(datetime.datetime.now().strftime(
                                                "%Y-%m-%d %M:%S -- ")) + "DEBUG: RECORD FILE NOT FOUND")
                                        else:
                                            continue
                                else:
                                    file_id[result['result']['Linkedid']] = 'NOANSWER'
                                    if settings.DEBUG:
                                        print(str(datetime.datetime.now().strftime(
                                            "%Y-%m-%d %M:%S -- ")) + "DEBUG: DID NOT GET ANSWER, NO RECORD FILE NEEDED")
                                    else:
                                        continue

                            if result['result']['Linkedid'] in lid:
                                if lid[result['result']['Linkedid']] != '':
                                    if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                            and ('NOANSWER' in file_id[result['result']['Linkedid']]) is False:
                                        payload[result['result']['Linkedid']] = {"context": {
                                            "status_zvonka": [{"code": "otvechen_1", "name": "📤Отвечен"}],
                                            "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                            "__name": str(client_number[result['result']['Linkedid']]),
                                            "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                            "poslednii_operator": operator[result['result']['Linkedid']][1],
                                            "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                            "svyazannye_lidy": [lid[result['result']['Linkedid']][0]],
                                            "record": [file_id[result['result']['Linkedid']]],
                                            "call_logs":
                                                {
                                                    "rows": rows
                                                }
                                        }
                                        }
                                    else:
                                        payload[result['result']['Linkedid']] = {"context": {
                                            "status_zvonka": [{"code": "ne_otvechen_1", "name": "🔺Не отвечен"}],
                                            "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                            "__name": str(client_number[result['result']['Linkedid']]),
                                            "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                            "poslednii_operator": operator[result['result']['Linkedid']][1],
                                            "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                            "svyazannye_lidy": [lid[result['result']['Linkedid']][0]],
                                            "call_logs":
                                                {
                                                    "rows": rows
                                                }
                                        }
                                        }
                                else:
                                    if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                            and ('NOANSWER' in file_id[result['result']['Linkedid']]) is False:
                                        payload[result['result']['Linkedid']] = {"context": {
                                            "status_zvonka": [{"code": "otvechen_1", "name": "📤Отвечен"}],
                                            "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                            "__name": str(client_number[result['result']['Linkedid']]),
                                            "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                            "poslednii_operator": operator[result['result']['Linkedid']][1],
                                            "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                            "record": [file_id[result['result']['Linkedid']]],
                                            "call_logs":
                                                {
                                                    "rows": rows
                                                }
                                        }
                                        }
                                    else:
                                        payload[result['result']['Linkedid']] = {"context": {
                                            "status_zvonka": [{"code": "ne_otvechen_1", "name": "🔺Не отвечен"}],
                                            "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                            "__name": str(client_number[result['result']['Linkedid']]),
                                            "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                            "poslednii_operator": operator[result['result']['Linkedid']][1],
                                            "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                            "call_logs":
                                                {
                                                    "rows": rows
                                                }
                                        }
                                        }

                            if settings.DEBUG:
                                print(str(datetime.datetime.now().strftime(
                                    "%Y-%m-%d %M:%S -- ")) + "DEBUG: PAYLOAD CONTEXT: " + str(
                                    payload[result['result']['Linkedid']]))
                            else:
                                continue
                            api_create_object = requests.post(settings.elma_settings['link'] + 'pub/v1/app/'
                                                              + settings.elma_settings['namespace'] + '/'
                                                              + settings.elma_settings['outgoing_calls'] + '/create',
                                                              data=json.dumps(payload[result['result']['Linkedid']]),
                                                              headers={
                                                                  'X-Token': settings.elma_settings['token'],
                                                              })

                            if settings.DEBUG:
                                print(str(datetime.datetime.now().strftime(
                                    "%Y-%m-%d %M:%S -- ")) + "DEBUG: API RESPONSE -- " + str(api_create_object.content))
                            else:
                                continue

                            outgoing_calls.pop(result['result']['Linkedid'], None)
                            client_number.pop(result['result']['Linkedid'], None)
                            operator.pop(result['result']['Linkedid'], None)
                            connected_line.pop(result['result']['Linkedid'], None)
                            end_timestamp.pop(result['result']['Linkedid'], None)
                            start_timestamp.pop(result['result']['Linkedid'], None)
                            event_timestamp.pop(result['result']['Linkedid'], None)
                            variables.pop(result['result']['Linkedid'], None)
                            item_dict.pop(result['result']['Linkedid'], None)
                            subscriber_name.pop(result['result']['Linkedid'], None)
                            start_timestamp.pop(result['result']['Linkedid'], None)
                            connected_line.pop(result['result']['Linkedid'], None)
                            end_timestamp.pop(result['result']['Linkedid'], None)
                            event_timestamp.pop(result['result']['Linkedid'], None)
                            event_name.pop(result['result']['Linkedid'], None)
                            dial_status.pop(result['result']['Linkedid'], None)
                            payload.pop(result['result']['Linkedid'], None)
                            login.pop(result['result']['Linkedid'], None)
                            lid.pop(result['result']['Linkedid'], None)
                            file_id.pop(result['result']['Linkedid'], None)

        except Exception:
            if settings.DEBUG:
                print(str(datetime.datetime.now().strftime("%Y-%m-%d %M:%S -- ")) + "DEBUG: ERROR -- " + str(Exception.with_traceback()))
                pass
            else:
                pass
        except json.decoder.JSONDecodeError as json_error:
            if settings.DEBUG:
                print(str(datetime.datetime.now().strftime(
                    "%Y-%m-%d %M:%S --")) + "DEBUG: JSON DECODER ERROR, ARGS: \n ERROR NAME: " + str(json_error)
                      + "\nLINE: " + str(event_string))
                pass
            else:
                pass

        current_string = ''