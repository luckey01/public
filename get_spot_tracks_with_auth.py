#!/usr/bin/env python3

import json
import pandas as pd
import requests
import urllib
import datetime
import base64

###########
#Input variables
###########
tracks_per_request = 50
total_offsets =  (1000 - tracks_per_request)/tracks_per_request
alphabet='acdefghijklmnopqrstuvwxyz'
i_already_completed = 0


###########
#DO NOT SHARE!!!
###########
client_id = {your-client-id}
client_secret = {your-client-secret}


###########
#Get access token
###########
def base64_encode(client_id,client_secret):
	message = client_id+':'+client_secret
	message_bytes = message.encode('ascii')
	base64_bytes = base64.b64encode(message_bytes)
	encodedData = base64_bytes.decode('ascii')
	return(encodedData)



def accesstoken(client_id, client_secret):
    header_string= base64_encode(client_id,client_secret)
    headers = {
        'Authorization': 'Basic '+header_string,
    }
    
    data = {
        'grant_type': 'client_credentials'
    }
    
    response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
    access_token = json.loads(response.text)['access_token']
    return(access_token)

access_token = accesstoken(client_id,client_secret)




###########
#build query letters
###########
queries=[]

for letter_first in alphabet :
    queries.append(letter_first)
    for letter_second in alphabet :
        queries.append(letter_first+letter_second)

total_queries = len(queries)

print('queries built, total query strings = '+str(total_queries))

###########
#build_offsets
###########
offsets = []

i=0
j=0
while i < total_offsets + 1 :
    offsets.append(j)
    i = i+1
    j = j+tracks_per_request
    
print('offsets built, total_offsets ='+str(len(offsets))) 
print('total requests = '+str(len(queries)*total_offsets))



###########
#FUNCITONS
###########

def get_tracks (full_response, query, offset, tracks_per_req) :
    response=json.loads(r.text)

    tracks_to_parse=response["tracks"]["items"]

    track_df = pd.DataFrame()

    i=0
    for track in tracks_to_parse :

        #id
        id=response["tracks"]['items'][i]['id']

        #song_name
        song_name=response["tracks"]['items'][i]['name']

        #artist_name
        artist_name=response["tracks"]['items'][i]['artists'][0]['name']

        #song_popularity
        song_popularity=response["tracks"]['items'][i]['popularity']

        #album_release_date
        album_release_date=response["tracks"]['items'][i]['album']['release_date']
        
        #song_explicit
        song_explicit=response["tracks"]['items'][i]['explicit']

        #total_available_markets
        total_available_markets=len(response["tracks"]['items'][i]['available_markets'])

        #is_local?
        is_local=response["tracks"]['items'][i]['is_local']
        

        track_dets = {'id': id,
                      'query' : query,
                      'offset' : offset,
                      'tracks_per_req' : tracks_per_req,
                      'song_name': song_name,
                      'artist_name': artist_name,
                      'song_popularity': song_popularity,
                      'album_release_date' : album_release_date,
                      'song_explicit': song_explicit,
                      'total_available_markets': total_available_markets,
                      'is_local': is_local}

        track_df=track_df.append(pd.DataFrame([track_dets]), sort=True)

        i = i+1
        
    track_df.reset_index()

    return track_df


def join_ids_with_commas (list_of_ids) :
    
    id_string=''
    
    for id in list_of_ids :
        id_string = id_string+str(id)+','
        
    return id_string

def join_and_encode (list_of_ids) :
    
    #join
    id_string=''
    
    for id in list_of_ids :
        id_string = id_string+str(id)+','
        
    id_string_encoded=urllib.quote(id_string)
        
    return id_string_encoded


def parse_aud_feats (response) :
    aud_feats = json.loads(r.text)['audio_features']

    df_aud_feats = pd.DataFrame()

    i=0
    for track in aud_feats :
        df_temp = pd.DataFrame([json.loads(r.text)['audio_features'][i]])
        df_aud_feats = df_aud_feats.append(df_temp, sort=True)
        i=i+1
        
    return df_aud_feats




###########
#MAKE REQUESTS
###########

complete_df=pd.DataFrame()


queries = queries[i_already_completed:]
tot_requests_remaining = len(queries)*total_offsets
print('total requests remaining = '+str(tot_requests_remaining))

name_for_output_df = 'spotify_tracks_from_query_'+str(queries[0]+'_no_'+str(i_already_completed)+'with_auth.csv')

i=i_already_completed
for query in queries :

    if i > i_already_completed :
        print(str(i)+' of '+str(total_queries)+' letter combos queried. '+'total tracks in df = '+str(len(complete_df))+'. last query string is '+str(query))


    i=i+1
    for offset in offsets:
    
        search_char=query



        #Get Tracks
        url = 'https://api.spotify.com/v1/search?q='+search_char+'%25&type=track&limit='+str(tracks_per_request)+'&offset='+str(offset)
        bear_tok = 'Bearer ' + access_token
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization' : bear_tok}
        r = requests.get(url, headers=headers)

        track_df=get_tracks(r, query, offset, tracks_per_request)



        # Get audio features
        ids = track_df['id']
        ids_joined_with_comma_encoded= join_and_encode(ids)

        url = "https://api.spotify.com/v1/audio-features?ids="+ids_joined_with_comma_encoded
        bear_tok = 'Bearer ' + access_token
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization' : bear_tok}
        r = requests.get(url, headers=headers)

        audio_feats_df=parse_aud_feats(r)



        #Merge track_df with analysis
        merged_df_from_this_query=pd.merge(track_df, audio_feats_df, left_on='id', right_on='id', sort=True)

        complete_df=complete_df.append(merged_df_from_this_query, sort=True).reset_index(drop=True)


        complete_df.to_csv(name_for_output_df ,encoding='utf-8')

print('total tracks = '+str(len(complete_df)))
print('head of all tracks')
print(complete_df.head())