' ============================================================
' ProcessOrder.vbs  — LEGACY VBScript File
' This is what we receive from the client's old system
' ============================================================

Dim conn
Set conn = CreateObject("ADODB.Connection")
conn.Open "DSN=OrdersDB"

Sub ProcessOrder(orderId, customerId, amount)
    Dim rs
    On Error Resume Next
    
    conn.Execute "UPDATE Orders SET Status='Processing' WHERE Id=" & orderId
    
    If Err.Number <> 0 Then
        MsgBox "Error processing order"
        Err.Clear
    End If
    
    ' Update customer balance
    conn.Execute "UPDATE Customers SET Balance=Balance-" & amount & " WHERE Id=" & customerId
    
    Set rs = Nothing
End Sub

Sub GetOrderTotal(orderId)
    Dim rs, total
    Set rs = conn.Execute("SELECT SUM(Price) as Total FROM OrderItems WHERE OrderId=" & orderId)
    
    If Not rs.EOF Then
        total = rs.Fields("Total")
        WScript.Echo "Total: " & total
    End If
    
    rs.Close
    Set rs = Nothing
End Sub

Sub CancelOrder(orderId, reason)
    Dim rs
    On Error Resume Next
    
    conn.Execute "UPDATE Orders SET Status='Cancelled', CancelReason='" & reason & "' WHERE Id=" & orderId
    conn.Execute "INSERT INTO AuditLog (OrderId, Action) VALUES (" & orderId & ", 'CANCEL')"
    
    Set rs = Nothing
End Sub
