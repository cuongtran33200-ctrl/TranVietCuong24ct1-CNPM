from django.http import HttpResponse

def home(request):
    return HttpResponse("""
        <html>
        <head>
            <title>CNPM-DAU</title>
        </head>

        <body style="
            margin: 0;
            font-family: Arial;
            background: linear-gradient(135deg, #667eea, #764ba2);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        ">

            <div style="
                background: white;
                padding: 50px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            ">

                <h1 style="color: #4f46e5;">
                    🎓 Chào bạn khóa 24CT
                </h1>

                <h2>
                    Đến với học phần CNPM-DAU
                </h2>

                <p>
                    Project: <b>24CT1-TRANVIETCUONG</b>
                </p>

                <p>
                    Framework: <b>Django</b>
                </p>

                <p>
                    Ngôn ngữ: <b>Python</b> 🐍
                </p>

            </div>

        </body>
        </html>
    """)