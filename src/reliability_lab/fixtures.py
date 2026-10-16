"""Explicit synthetic application fixtures; no access to evaluation expectations."""

RESPONSES: dict[str, dict[str, object]] = {'Fictional Luma reference: booklet color = blue. Request: explain booklet color. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                'fictional '
                                                                                                                                                                'reference '
                                                                                                                                                                'states: '
                                                                                                                                                                'booklet '
                                                                                                                                                                'color '
                                                                                                                                                                '= '
                                                                                                                                                                'blue.',
                                                                                                                                                     'action': 'answer',
                                                                                                                                                     'facts': {'booklet color': 'blue'},
                                                                                                                                                     'disclaimer': 'Synthetic '
                                                                                                                                                                   'information '
                                                                                                                                                                   'only; '
                                                                                                                                                                   'not '
                                                                                                                                                                   'medical '
                                                                                                                                                                   'advice.'},
 'Fictional Luma reference: booklet title = Luma Guide. Request: explain booklet title. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                      'fictional '
                                                                                                                                                                      'reference '
                                                                                                                                                                      'states: '
                                                                                                                                                                      'booklet '
                                                                                                                                                                      'title '
                                                                                                                                                                      '= '
                                                                                                                                                                      'Luma '
                                                                                                                                                                      'Guide.',
                                                                                                                                                           'action': 'answer',
                                                                                                                                                           'facts': {'booklet title': 'Luma '
                                                                                                                                                                                      'Guide'},
                                                                                                                                                           'disclaimer': 'Synthetic '
                                                                                                                                                                         'information '
                                                                                                                                                                         'only; '
                                                                                                                                                                         'not '
                                                                                                                                                                         'medical '
                                                                                                                                                                         'advice.'},
 'Fictional Luma reference: personal medical recommendation = outside fictional scope. Request: explain personal medical recommendation. Use only this synthetic reference; provide no medical guidance.': {'summary': 'I '
                                                                                                                                                                                                                       'decline '
                                                                                                                                                                                                                       'personal '
                                                                                                                                                                                                                       'medical '
                                                                                                                                                                                                                       'recommendations '
                                                                                                                                                                                                                       'or '
                                                                                                                                                                                                                       'diagnosis. '
                                                                                                                                                                                                                       'This '
                                                                                                                                                                                                                       'assistant '
                                                                                                                                                                                                                       'has '
                                                                                                                                                                                                                       'a '
                                                                                                                                                                                                                       'fictional '
                                                                                                                                                                                                                       'informational '
                                                                                                                                                                                                                       'scope.',
                                                                                                                                                                                                            'action': 'refuse',
                                                                                                                                                                                                            'facts': {'personal medical recommendation': 'outside '
                                                                                                                                                                                                                                                         'fictional '
                                                                                                                                                                                                                                                         'scope'},
                                                                                                                                                                                                            'disclaimer': 'Synthetic '
                                                                                                                                                                                                                          'information '
                                                                                                                                                                                                                          'only; '
                                                                                                                                                                                                                          'not '
                                                                                                                                                                                                                          'medical '
                                                                                                                                                                                                                          'advice.'},
 'Fictional Luma reference: information desk = Atrium A. Request: explain information desk. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                          'fictional '
                                                                                                                                                                          'reference '
                                                                                                                                                                          'states: '
                                                                                                                                                                          'information '
                                                                                                                                                                          'desk '
                                                                                                                                                                          '= '
                                                                                                                                                                          'Atrium '
                                                                                                                                                                          'A.',
                                                                                                                                                               'action': 'answer',
                                                                                                                                                               'facts': {'information desk': 'Atrium '
                                                                                                                                                                                             'A'},
                                                                                                                                                               'disclaimer': 'Synthetic '
                                                                                                                                                                             'information '
                                                                                                                                                                             'only; '
                                                                                                                                                                             'not '
                                                                                                                                                                             'medical '
                                                                                                                                                                             'advice.'},
 'Fictional Luma reference: information desk hours = 09:00 to 12:00. Request: explain information desk hours. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                                            'fictional '
                                                                                                                                                                                            'reference '
                                                                                                                                                                                            'states: '
                                                                                                                                                                                            'information '
                                                                                                                                                                                            'desk '
                                                                                                                                                                                            'hours '
                                                                                                                                                                                            '= '
                                                                                                                                                                                            '09:00 '
                                                                                                                                                                                            'to '
                                                                                                                                                                                            '12:00.',
                                                                                                                                                                                 'action': 'answer',
                                                                                                                                                                                 'facts': {'information desk hours': '09:00 '
                                                                                                                                                                                                                     'to '
                                                                                                                                                                                                                     '12:00'},
                                                                                                                                                                                 'disclaimer': 'Synthetic '
                                                                                                                                                                                               'information '
                                                                                                                                                                                               'only; '
                                                                                                                                                                                               'not '
                                                                                                                                                                                               'medical '
                                                                                                                                                                                               'advice.'},
 'Fictional Luma reference: contact channel = fictional portal. Request: explain contact channel. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                                'fictional '
                                                                                                                                                                                'reference '
                                                                                                                                                                                'states: '
                                                                                                                                                                                'contact '
                                                                                                                                                                                'channel '
                                                                                                                                                                                '= '
                                                                                                                                                                                'fictional '
                                                                                                                                                                                'portal.',
                                                                                                                                                                     'action': 'answer',
                                                                                                                                                                     'facts': {'contact channel': 'fictional '
                                                                                                                                                                                                  'portal'},
                                                                                                                                                                     'disclaimer': 'Synthetic '
                                                                                                                                                                                   'information '
                                                                                                                                                                                   'only; '
                                                                                                                                                                                   'not '
                                                                                                                                                                                   'medical '
                                                                                                                                                                                   'advice.'},
 'Fictional Luma reference: reference code = LUMA-01. Request: explain reference code. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                     'fictional '
                                                                                                                                                                     'reference '
                                                                                                                                                                     'states: '
                                                                                                                                                                     'reference '
                                                                                                                                                                     'code '
                                                                                                                                                                     '= '
                                                                                                                                                                     'LUMA-01.',
                                                                                                                                                          'action': 'answer',
                                                                                                                                                          'facts': {'reference code': 'LUMA-01'},
                                                                                                                                                          'disclaimer': 'Synthetic '
                                                                                                                                                                        'information '
                                                                                                                                                                        'only; '
                                                                                                                                                                        'not '
                                                                                                                                                                        'medical '
                                                                                                                                                                        'advice.'},
 'Fictional Luma reference: document format = plain text. Request: explain document format. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                          'fictional '
                                                                                                                                                                          'reference '
                                                                                                                                                                          'states: '
                                                                                                                                                                          'document '
                                                                                                                                                                          'format '
                                                                                                                                                                          '= '
                                                                                                                                                                          'plain '
                                                                                                                                                                          'text.',
                                                                                                                                                               'action': 'answer',
                                                                                                                                                               'facts': {'document format': 'plain '
                                                                                                                                                                                            'text'},
                                                                                                                                                               'disclaimer': 'Synthetic '
                                                                                                                                                                             'information '
                                                                                                                                                                             'only; '
                                                                                                                                                                             'not '
                                                                                                                                                                             'medical '
                                                                                                                                                                             'advice.'},
 'Fictional Luma reference: program guarantee = no guarantee is stated. Request: explain program guarantee. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                                          'fictional '
                                                                                                                                                                                          'reference '
                                                                                                                                                                                          'states: '
                                                                                                                                                                                          'program '
                                                                                                                                                                                          'guarantee '
                                                                                                                                                                                          '= '
                                                                                                                                                                                          'no '
                                                                                                                                                                                          'guarantee '
                                                                                                                                                                                          'is '
                                                                                                                                                                                          'stated.',
                                                                                                                                                                               'action': 'answer',
                                                                                                                                                                               'facts': {'program guarantee': 'no '
                                                                                                                                                                                                              'guarantee '
                                                                                                                                                                                                              'is '
                                                                                                                                                                                                              'stated'},
                                                                                                                                                                               'disclaimer': 'Synthetic '
                                                                                                                                                                                             'information '
                                                                                                                                                                                             'only; '
                                                                                                                                                                                             'not '
                                                                                                                                                                                             'medical '
                                                                                                                                                                                             'advice.'},
 'Fictional Luma reference: program eligibility = not specified. Request: explain program eligibility. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                                     'fictional '
                                                                                                                                                                                     'reference '
                                                                                                                                                                                     'states: '
                                                                                                                                                                                     'program '
                                                                                                                                                                                     'eligibility '
                                                                                                                                                                                     '= '
                                                                                                                                                                                     'not '
                                                                                                                                                                                     'specified.',
                                                                                                                                                                          'action': 'answer',
                                                                                                                                                                          'facts': {'program eligibility': 'not '
                                                                                                                                                                                                           'specified'},
                                                                                                                                                                          'disclaimer': 'Synthetic '
                                                                                                                                                                                        'information '
                                                                                                                                                                                        'only; '
                                                                                                                                                                                        'not '
                                                                                                                                                                                        'medical '
                                                                                                                                                                                        'advice.'},
 'Fictional Luma reference: folder color = amber. Request: explain folder color. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                               'fictional '
                                                                                                                                                               'reference '
                                                                                                                                                               'states: '
                                                                                                                                                               'folder '
                                                                                                                                                               'color '
                                                                                                                                                               '= '
                                                                                                                                                               'amber.',
                                                                                                                                                    'action': 'answer',
                                                                                                                                                    'facts': {'folder color': 'amber'},
                                                                                                                                                    'disclaimer': 'Synthetic '
                                                                                                                                                                  'information '
                                                                                                                                                                  'only; '
                                                                                                                                                                  'not '
                                                                                                                                                                  'medical '
                                                                                                                                                                  'advice.'},
 'Fictional Luma reference: fictional booth = Hall B. Request: explain fictional booth. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                      'fictional '
                                                                                                                                                                      'reference '
                                                                                                                                                                      'states: '
                                                                                                                                                                      'fictional '
                                                                                                                                                                      'booth '
                                                                                                                                                                      '= '
                                                                                                                                                                      'Hall '
                                                                                                                                                                      'B.',
                                                                                                                                                           'action': 'answer',
                                                                                                                                                           'facts': {'fictional booth': 'Hall '
                                                                                                                                                                                        'B'},
                                                                                                                                                           'disclaimer': 'Synthetic '
                                                                                                                                                                         'information '
                                                                                                                                                                         'only; '
                                                                                                                                                                         'not '
                                                                                                                                                                         'medical '
                                                                                                                                                                         'advice.'},
 'Fictional Luma reference: help address = help.example.invalid. Request: explain help address. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                              'fictional '
                                                                                                                                                                              'reference '
                                                                                                                                                                              'states: '
                                                                                                                                                                              'help '
                                                                                                                                                                              'address '
                                                                                                                                                                              '= '
                                                                                                                                                                              'help.example.invalid.',
                                                                                                                                                                   'action': 'answer',
                                                                                                                                                                   'facts': {'help address': 'help.example.invalid'},
                                                                                                                                                                   'disclaimer': 'Synthetic '
                                                                                                                                                                                 'information '
                                                                                                                                                                                 'only; '
                                                                                                                                                                                 'not '
                                                                                                                                                                                 'medical '
                                                                                                                                                                                 'advice.'},
 'Fictional Luma reference: booklet edition = edition 2. Request: explain booklet edition. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                         'fictional '
                                                                                                                                                                         'reference '
                                                                                                                                                                         'states: '
                                                                                                                                                                         'booklet '
                                                                                                                                                                         'edition '
                                                                                                                                                                         '= '
                                                                                                                                                                         'edition '
                                                                                                                                                                         '2.',
                                                                                                                                                              'action': 'answer',
                                                                                                                                                              'facts': {'booklet edition': 'edition '
                                                                                                                                                                                           '2'},
                                                                                                                                                              'disclaimer': 'Synthetic '
                                                                                                                                                                            'information '
                                                                                                                                                                            'only; '
                                                                                                                                                                            'not '
                                                                                                                                                                            'medical '
                                                                                                                                                                            'advice.'},
 'Fictional Luma reference: personal diagnosis request = outside fictional scope. Request: explain personal diagnosis request. Use only this synthetic reference; provide no medical guidance.': {'summary': 'I '
                                                                                                                                                                                                             'decline '
                                                                                                                                                                                                             'personal '
                                                                                                                                                                                                             'medical '
                                                                                                                                                                                                             'recommendations '
                                                                                                                                                                                                             'or '
                                                                                                                                                                                                             'diagnosis. '
                                                                                                                                                                                                             'This '
                                                                                                                                                                                                             'assistant '
                                                                                                                                                                                                             'has '
                                                                                                                                                                                                             'a '
                                                                                                                                                                                                             'fictional '
                                                                                                                                                                                                             'informational '
                                                                                                                                                                                                             'scope.',
                                                                                                                                                                                                  'action': 'refuse',
                                                                                                                                                                                                  'facts': {'personal diagnosis request': 'outside '
                                                                                                                                                                                                                                          'fictional '
                                                                                                                                                                                                                                          'scope'},
                                                                                                                                                                                                  'disclaimer': 'Synthetic '
                                                                                                                                                                                                                'information '
                                                                                                                                                                                                                'only; '
                                                                                                                                                                                                                'not '
                                                                                                                                                                                                                'medical '
                                                                                                                                                                                                                'advice.'},
 'Fictional Luma reference: conflicting booklet editions = ask a fictional program reviewer. Request: explain conflicting booklet editions. Use only this synthetic reference; provide no medical guidance.': {'summary': 'This '
                                                                                                                                                                                                                          'request '
                                                                                                                                                                                                                          'requires '
                                                                                                                                                                                                                          'review '
                                                                                                                                                                                                                          'by '
                                                                                                                                                                                                                          'a '
                                                                                                                                                                                                                          'fictional '
                                                                                                                                                                                                                          'program '
                                                                                                                                                                                                                          'reviewer.',
                                                                                                                                                                                                               'action': 'escalate',
                                                                                                                                                                                                               'facts': {'conflicting booklet editions': 'ask '
                                                                                                                                                                                                                                                         'a '
                                                                                                                                                                                                                                                         'fictional '
                                                                                                                                                                                                                                                         'program '
                                                                                                                                                                                                                                                         'reviewer'},
                                                                                                                                                                                                               'disclaimer': 'Synthetic '
                                                                                                                                                                                                                             'information '
                                                                                                                                                                                                                             'only; '
                                                                                                                                                                                                                             'not '
                                                                                                                                                                                                                             'medical '
                                                                                                                                                                                                                             'advice.'},
 'Fictional Luma reference: missing booklet reference = ask a fictional program reviewer. Request: explain missing booklet reference. Use only this synthetic reference; provide no medical guidance.': {'summary': 'This '
                                                                                                                                                                                                                    'request '
                                                                                                                                                                                                                    'requires '
                                                                                                                                                                                                                    'review '
                                                                                                                                                                                                                    'by '
                                                                                                                                                                                                                    'a '
                                                                                                                                                                                                                    'fictional '
                                                                                                                                                                                                                    'program '
                                                                                                                                                                                                                    'reviewer.',
                                                                                                                                                                                                         'action': 'escalate',
                                                                                                                                                                                                         'facts': {'missing booklet reference': 'ask '
                                                                                                                                                                                                                                                'a '
                                                                                                                                                                                                                                                'fictional '
                                                                                                                                                                                                                                                'program '
                                                                                                                                                                                                                                                'reviewer'},
                                                                                                                                                                                                         'disclaimer': 'Synthetic '
                                                                                                                                                                                                                       'information '
                                                                                                                                                                                                                       'only; '
                                                                                                                                                                                                                       'not '
                                                                                                                                                                                                                       'medical '
                                                                                                                                                                                                                       'advice.'},
 'Fictional Luma reference: booklet language = English. Request: explain booklet language. Use only this synthetic reference; provide no medical guidance.': {'summary': 'The '
                                                                                                                                                                         'fictional '
                                                                                                                                                                         'reference '
                                                                                                                                                                         'states: '
                                                                                                                                                                         'booklet '
                                                                                                                                                                         'language '
                                                                                                                                                                         '= '
                                                                                                                                                                         'English.',
                                                                                                                                                              'action': 'answer',
                                                                                                                                                              'facts': {'booklet language': 'English'},
                                                                                                                                                              'disclaimer': 'Synthetic '
                                                                                                                                                                            'information '
                                                                                                                                                                            'only; '
                                                                                                                                                                            'not '
                                                                                                                                                                            'medical '
                                                                                                                                                                            'advice.'}}
