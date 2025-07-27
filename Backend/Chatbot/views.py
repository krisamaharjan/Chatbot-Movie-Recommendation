import ollama
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import re

# TMDB API Configuration (replace with your actual key)
TMDB_API_KEY = config('Movie-key') # 

@csrf_exempt
def recommend_movies(request):
    if request.method == 'POST':
        raw_query = request.POST.get('query', '').strip()
        
        if not raw_query:
            return JsonResponse({'error': 'Please enter a movie request'}, status=400)
        
        # Step 1: Understand user intent
        query_type, clean_query = analyze_query(raw_query.lower())
        
        # Step 2: Get movies from TMDB
        try:
            movies = fetch_movies(query_type, clean_query)
            if not movies:
                return JsonResponse({'response': "No movies found. Try something like 'action movies' or 'sad films'"})
            
            # Step 3: Generate TinyLlama response
            response_text = generate_response(raw_query, movies)
            
            return JsonResponse({
                'response': response_text,
                'movies': [{
                    'title': m['title'],
                    'year': m.get('release_date', '')[:4],
                    'rating': m.get('vote_average', 0),
                    'overview': m.get('overview', '')
                } for m in movies]
            })
            
        except Exception as e:
            return JsonResponse({'error': f"Oops! Something went wrong: {str(e)}"}, status=500)
    
    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

# Helper Functions
def analyze_query(query):
    """Determine what type of movie query this is"""
    # Check for number requests ("5 movies")
    if count_match := re.search(r'(\d+)\s*movies?', query):
        return ('count', int(count_match.group(1)))
    
    # Genre detection
    genres = ['romance', 'comedy', 'horror', 'sci-fi', 'action', 
              'drama', 'thriller', 'adventure', 'fantasy']
    for genre in genres:
        if genre in query:
            return ('genre', genre)
    
    # Mood detection
    mood_map = {
        'sad': 'drama',
        'happy': 'comedy',
        'scared': 'horror',
        'romantic': 'romance'
    }
    for mood, genre in mood_map.items():
        if mood in query:
            return ('mood', genre)
    
    return ('search', query)  # Default to standard search

def fetch_movies(query_type, query_param):
    """Fetch movies from TMDB based on query type"""
    if query_type == 'genre':
        url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}"
        url += f"&with_genres={get_genre_id(query_param)}&sort_by=popularity.desc"
    elif query_type == 'count':
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}"
        movies = requests.get(url).json().get('results', [])[:query_param]
    elif query_type == 'mood':
        url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}"
        url += f"&with_genres={get_genre_id(query_param)}&sort_by=vote_average.desc"
    else:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query_param}"
    
    movies = requests.get(url).json().get('results', [])[:5]

    # Fetch cast and crew details
    for movie in movies:
        cast, director = fetch_cast_and_crew(movie['id'])
        movie['cast'] = cast
        movie['director'] = director

    return movies

def fetch_cast_and_crew(movie_id):
    """Fetch top 3 cast and director from TMDB credits endpoint"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
    try:
        data = requests.get(url).json()
        cast_names = [member['name'] for member in data.get('cast', [])[:3]]
        director_name = next((crew['name'] for crew in data.get('crew', []) if crew['job'] == 'Director'), 'Unknown')
        return cast_names, director_name
    except:
        return [], 'Unknown'

def get_genre_id(genre_name):
    """Convert genre name to TMDB ID"""
    genre_ids = {
        'action': 28, 'adventure': 12, 'animation': 16, 
        'comedy': 35, 'crime': 80, 'documentary': 99,
        'drama': 18, 'family': 10751, 'fantasy': 14,
        'history': 36, 'horror': 27, 'music': 10402,
        'mystery': 9648, 'romance': 10749, 'sci-fi': 878,
        'thriller': 53, 'war': 10752, 'western': 37
    }
    return genre_ids.get(genre_name, 18)  # Default to Drama

def generate_response(user_query, movies):
    """Generate conversational response using TinyLlama"""
    movie_list = "\n".join(
        f"{idx+1}. {m['title']} ({m.get('release_date', '?')[:4]}) ★{m.get('vote_average', '?')}\n"
        f"   Cast: {', '.join(m.get('cast', []))}\n"
        f"   Director: {m.get('director', 'Unknown')}"
        for idx, m in enumerate(movies)
    )
    
    prompt = f"""You are a movie recommendation assistant.
Recommended movies based on the user query:
{movie_list}

Respond in 2 sentences:
1. Acknowledge the request naturally.
2. Highlight the top recommendation and one cast or director fact."""
    
    try:
        response = ollama.chat(
            model='tinyllama',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.7, 'num_predict': 700}
        )
        return response['message']['content']
    except:
        top_movie = movies[0]
        return (
            f"I think you'll enjoy '{top_movie['title']}' "
            f"(rated {top_movie.get('vote_average', '?')}/10), directed by {top_movie.get('director', 'Unknown')}. "
            f"Main cast includes {', '.join(top_movie.get('cast', [])[:2])}."
        )