import base64
import datetime
import io

from requests.exceptions import SSLError

import dash
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash_bootstrap_components._components.Row import Row
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

import pandas as pd
from ipdb import set_trace as st

from NewspaperScrape import NewspaperScrape, ProgressCounter

# df = None
ns = None
progress_bar_value = ProgressCounter()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY]
)

app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            [
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    # Allow multiple files to be uploaded
                    multiple=True
                ),
                html.Div(id='output-data-upload'),
            ],
            width=12
        )
    ),
    dbc.Row(
        dbc.Col(
            [
                dbc.Progress(
                    id="progress-bar",
                    value=progress_bar_value.counter,
                    striped=True,
                    color="success",
                    animated=True,
                    style={
                        "margin": "10px",
                        "height": "30px",
                        "font-size": "15px"
                    }
                )
            ],
            width=12
        ),
    ),
    dbc.Row([
        dbc.Col(
            dbc.Button(
                "Download Content",
                id="content-download-btn",
                n_clicks=0,
                color="primary",
                disabled=True
            ),
            width=2
        ),
        dbc.Col(
            dbc.Button(
                "Analyze Content",
                id="content-analyze-btn",
                n_clicks=0,
                color="primary",
                disabled=False
            ),
            width=2
        )],
        justify="center"
    ),
    dbc.Row([
        dbc.Col(
            dash_table.DataTable(
                id={
                    "type": "datatable-analyze",
                    "index": 1
                },
                # id="datatable",
                data=None,
                # ns.df.to_dict('records')
                columns=None,
                # [{'name': i, 'id': i} for i in ns.df.columns]
                style_cell={
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': 0,
                    'textAlign': 'left'
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': c},
                        'textAlign': 'left'
                    } for c in ['Date', 'Region']
                ],
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                page_action="native",
                page_current=0,
                page_size=10
            ),
        )
    ]),
    dcc.Interval(
        id='interval-component',
        interval=1*1000, # in milliseconds
        n_intervals=0
    )
])


def parse_contents(contents, filename, date):
    global ns
    content_type, content_string = contents.split(',')
    df = None
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    ns = NewspaperScrape(
        output_dir=None,
        dataframe=df,
        num_rows=8
    )

    return html.Div([
        html.H5(filename),
        # html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            id={
                "type": "datatable_download",
                "index": 1
            },
            # id="datatable",
            data=ns.df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in ns.df.columns],
            style_cell={
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 0,
                'textAlign': 'left'
            },
            style_cell_conditional=[
                {
                    'if': {'column_id': c},
                    'textAlign': 'left'
                } for c in ['Date', 'Region']
            ],
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            page_action="native",
            page_current=0,
            page_size=10
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        # html.Div('Raw Content'),
        # html.Pre(contents[0:200] + '...', style={
        #     'whiteSpace': 'pre-wrap',
        #     'wordBreak': 'break-all'
        # })
    ])


@app.callback(
    [
        Output('output-data-upload', 'children'),
        Output("content-download-btn", 'disabled'),
    ],
    [
        Input('upload-data', 'contents'),
        # Input('content-download-btn', 'n_clicks')
    ],
    [
        State('upload-data', 'filename'),
        State('upload-data', 'last_modified')
    ]
)
def upload_data(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return [children, False]
    else:
        raise PreventUpdate


@app.callback(
    [
        Output({
            "type": "datatable_download",
            "index": MATCH
        }, 'data'),
        Output({
            "type": "datatable_download",
            "index": MATCH
        }, 'columns'),
        # Output({
        #     "type": "content-analyze-btn",
        #     "index": MATCH
        # }, "disabled")

    ],
    # ADD DATATABLE IDD!!!!!!!!!
    [Input('content-download-btn', 'n_clicks')],
)
def update_output(n_clicks):
    global ns
    if n_clicks == 0:
        raise PreventUpdate
    else:
        # st()
        ns.download_all(progress_bar_value)
        return [
            ns.df.to_dict('records'),
            [{'name': i, 'id': i} for i in ns.df.columns],
            # False
        ]

@app.callback(
    [
        Output('progress-bar', 'value'),
        Output('progress-bar', 'children')
    ],
    [Input('interval-component', 'n_intervals')]
)
def update_graph_live(n):
    global ns
    if ns is None:
        raise PreventUpdate
    else:
        percentage = progress_bar_value.counter * 100 / len(ns.df)
        return [
            round(percentage),
            f"{progress_bar_value.counter}/{len(ns.df)} ({percentage:.1f}%)"
        ]


@app.callback(
    [
        Output({
            "type": "datatable-analyze",
            "index": MATCH
        }, 'data'),
        Output({
            "type": "datatable-analyze",
            "index": MATCH
        }, 'columns'),
    ],
    [Input('content-analyze-btn', 'n_clicks')],
)
def update_graph_live(n_clicks):
    global ns
    if n_clicks == 0:
        raise PreventUpdate
    else:
        ns.get_all_lemmas()
        ns.analyze()
        return [
            ns.analyzed_df.to_dict('records'),
            [{'name': i, 'id': i} for i in ns.analyzed_df.columns],
        ]


if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=5001)

# if __name__ == '__main__':
#     app.run_server(debug=True)
