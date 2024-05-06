<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: sans-serif;
            line-height: 1.5;
            color: #111827;
            margin: 0;
            padding: 0;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding: 1.25rem 2.5rem;
        }
        hr {
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 0;
        }
        section {
            padding: 1.25rem 2.5rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 0.75rem 1rem;
            border-bottom: 2px solid #e5e7eb;
        }
        th {
            text-align: left;
            text-transform: uppercase;
            font-weight: bold;
            font-size: 1rem;
            color: black;
            background-color: lightgrey;
            border-bottom: none;
        }
        td {
            font-size: 1rem;
            color: #111827;
        }
        .text-right {
            text-align: right;
        }
        .bg-gray-50 {
            background-color: #ffffff !important;
        }
        .bg-white {
            background-color: #ffffff;
        }
        .font-medium {
            font-weight: 500;
        }
        .text-xs {
            font-size: 1rem;
        }
    </style>
    <title>Sales Report | Style-x shirts</title>
</head>
<body>
    <div class="max-w-7xl mx-auto">
        <header>
            <h1 style="font-size: 2.25rem; line-height: 1.1;" class="text-gray-900">Sales Report</h1>
        </header>         

        <hr>

        <section>
            <p class="text-xs">
                <strong>Company Name:</strong>
                {{ shop.company_name }}
                <br />
                <strong>Date Generated:</strong>
                {{ date_generated }}
            </p>
        </section>

        <hr>

        <section style="display: flex; justify-content: space-between;">
            <p class="text-xs">
                <strong>Address:</strong><br>
                {{ shop.company_address|safe }}
            </p>

            <p class="text-xs text-right">
                <strong>Contact Details:</strong><br>
                {{ shop.company_contact }}<br>
                {{ shop.company_email }}            
            </p>
        </section>
<section>
            <div>
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Order Date</th>
                            <th>Customer Name</th>
                            <th class="text-right">Email</th>
                            <th class="text-right">Mobile Number</th>
                            <th class="text-right">Amount</th>
                            <th class="text-right">Payment Method</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for record in records %}
                        <tr class="bg-white">
                            <td>{{ record.id }}</td>
                            <td>{{  record.created_at|date:"d/m/Y"}}</td>
                            <td>{{ record.user.user_fname }} {{ record.user.user_lname }}</td>
                            <td>{{ record.user.user_email }}</td>
                            <td >{{ record.user.user_contact }}</td>
                            <td >{{ record.total_price }}</td>
                            <td >{{ record.payment_method }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>