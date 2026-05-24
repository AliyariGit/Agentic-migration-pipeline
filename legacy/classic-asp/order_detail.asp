<%
' ============================================================
' order_detail.asp  — LEGACY Classic ASP File
' This is what we receive from the client's old system
' ============================================================

Dim conn, rs, orderId, customerName, total

orderId = Request.Form("OrderId")

' --- SQL DATA ACCESS LAYER (will become EF Core) ---
Set conn = Server.CreateObject("ADODB.Connection")
conn.Open "DSN=OrdersDB"

Set rs = conn.Execute("SELECT o.*, c.Name FROM Orders o JOIN Customers c ON o.CustomerId=c.Id WHERE o.Id=" & orderId)

If Not rs.EOF Then
    customerName = rs("Name")
    total = rs("Total")
End If

' Fetch order items
Dim itemsRS
Set itemsRS = conn.Execute("SELECT * FROM OrderItems WHERE OrderId=" & orderId)

%>

<!-- UI / RESPONSE LAYER (will become Razor View + ViewModel) -->
<html>
<body>

<h1>Order Detail</h1>

<%
' Business logic mixed into UI layer (violation — will be moved to Service)
If Session("UserRole") = "Admin" Then
    Response.Write("<p>Admin View: Customer = " & customerName & "</p>")
End If

Response.Write("<p>Order ID: " & orderId & "</p>")
Response.Write("<p>Customer: " & customerName & "</p>")
Response.Write("<p>Total: $" & total & "</p>")

Do While Not itemsRS.EOF
    Response.Write("<li>" & itemsRS("ProductName") & " - $" & itemsRS("Price") & "</li>")
    itemsRS.MoveNext
Loop
%>

<form method="post" action="cancel_order.asp">
    <input type="hidden" name="OrderId" value="<% = orderId %>">
    <input type="submit" value="Cancel Order">
</form>

</body>
</html>
