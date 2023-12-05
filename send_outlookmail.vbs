Const olByValue = 1
Const olMailItem = 0
    
Dim oOApp 
Dim oOMail

Set oOApp = CreateObject("Outlook.Application")
Set oOMail = oOApp.CreateItem(olMailItem)

With oOMail
    .To = "steffen@koehlers.de"
    .Subject = "Unser t�glicher Daten- Extrakt"
    .Body = "Daten siehe Attachment"
    .Attachments.Add Wscript.Arguments(0), olByValue, 1
    .Send
End With