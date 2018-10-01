 function addTable(){
    $("#myTable").empty();
    var dbName=document.getElementById("db_list");
    var list1=document.getElementById("list1");
    var list2=document.getElementById("list2");
    var list3=document.getElementById("list3");
    var quantity=document.getElementById("quantity");

if(dbName.value!="" && quantity.value!="" && list1.value!="" && list2.value!="" && list3.value!=""){

    var myTableDiv=document.getElementById("myTable");

    var table = document.createElement('TABLE');
    table.border='1';
    var tableBody = document.createElement('TBODY');
    table.appendChild(tableBody);

    var tr=document.createElement('TR');
    tableBody.appendChild(tr);

    var td=document.createElement('TD');
    td.width='75';
    td.appendChild(document.createTextNode(dbName.value));
    tr.appendChild(td);
    var td=document.createElement('TD');
    td.width='75';
    td.appendChild(document.createTextNode(list1.value));
    tr.appendChild(td);
    var td=document.createElement('TD');
    td.width='75';
    td.appendChild(document.createTextNode(list2.value));
    tr.appendChild(td);
    var td=document.createElement('TD');
    td.width='75';
    td.appendChild(document.createTextNode(list3.value));
    tr.appendChild(td);
    var td=document.createElement('TD');
    td.width='75';
    td.appendChild(document.createTextNode(quantity.value));
    tr.appendChild(td);

    myTableDiv.appendChild(table);
    document.getElementById("grid").style.display="block";
    }

    else{
    alert("enter all fields");}
}