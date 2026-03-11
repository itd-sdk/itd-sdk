from itd import ITDClient

c = ITDClient(cookies=input('token: '))

with open('nowkie.gif', 'rb') as f:
    file_data = f.read()

file_data = file_data.replace(b'\x00\x3b', b'\xee\x3b') # можно менять "\xff" (диапазон 00-ff, например 9b)
file = c.upload_file('itd-sdk.gif', file_data)
if file.mime_type == 'image/jpeg':
    print('not converted to GIF! Increase replacing value ("\\xff")')
    quit()

print('link', file.url)

c.add_comment('fd64eec8-8db3-4d36-83d2-e020a37e43b4','я тоже так умею', attachment_ids=[file.id])