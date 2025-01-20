# IDEforWebServices
Two students trying to make a "Web Service" where you can code like you are on Google Docs

## How to run the code 
To run the code from the root 
```bash 
docker-compose up
```

full command to clear the cache and build the docker
```bash 
docker-compose down -v && docker-compose build --no-cache && docker-compose up
```

>[!WARNING]
> If the C compiler doesen't work you need to change the CHMODE of the ide_projects file with this command
>
```bash 
chmod 777 ide_projects
```

# Collaboration Recommendation System

## Overview
This system helps match users for collaboration based on their skills, experience, and availability. It uses a sophisticated scoring algorithm that considers multiple factors to find the most compatible collaborators.

## Scoring System

### Components and Weights
The final compatibility score is calculated using three main components:

- **Skills Compatibility (50%)**: Evaluates the match between users' specific skills
- **Experience Level (30%)**: Compares overall experience levels and years of experience
- **Availability (20%)**: Matches preferred working hours

### Detailed Scoring Criteria

#### 1. Skills Compatibility Score
- Compares individual skills within each domain
- For each matching skill, evaluates:
  - Skill level difference
  - Years of experience (capped at 10 years)
- Uses RMSE (Root Mean Square Error) for calculation
- Higher similarity results in a higher score
- Skills not found in both users' profiles are not considered

#### 2. Experience Level Score
Experience levels are mapped as follows:
- Junior: 1 point
- Intermediate: 2 points
- Senior: 3 points
- Expert: 4 points

The score considers:
- Difference in experience levels
- Difference in total years of experience (capped at 10 years)
- Uses RMSE for calculation

#### 3. Availability Score
- 100 points: Users have matching preferred working hours
- 50 points: Users have different preferred working hours

## Eligibility Criteria
Users are only considered for recommendations if they:
- Are not the same user
- Have marked themselves as "Available" for collaboration

## Score Calculation
1. Each component score is calculated independently
2. Scores are weighted according to their importance
3. Final score = (Skills Score × 0.5) + (Experience Score × 0.3) + (Availability Score × 0.2)
4. Results are rounded to 2 decimal places
5. Final scores range from 0 to 100, where 100 represents perfect compatibility


## Performance Considerations
- The system calculates scores for all available users in the database
- Complexity scales linearly with the number of users
- Skills comparison is optimized using dictionary lookups
  
## Algorithms for the Recomandation 

```python
def recommend_by_experience(user):
    """
    Recommande des collaborateurs basés sur le RMSE des niveaux d'expérience
    et des compétences
    """
    # Trouver tous les utilisateurs potentiels
    potential_collaborators = db.user_data.find({
        "_id": {"$ne": user["_id"]},
        "availability_for_collaboration": "Available"
    }, {"password": 0})
    
    recommendations = []
    for collaborator in potential_collaborators:
        # Calculer le score RMSE pour les compétences
        skills_score = calculate_rmse_score(user["skills"], collaborator["skills"])
        
        # Calculer le score RMSE pour l'expérience globale
        experience_score = calculate_experience_rmse(user, collaborator)
        
        # Calculer le score de disponibilité
        availability_score = 100 if (
            collaborator["preferred_working_hours"] == user["preferred_working_hours"]
        ) else 50
        
        # Calculer le score final pondéré
        final_score = (
            skills_score * 0.5 +          # Les compétences comptent pour 50%
            experience_score * 0.3 +       # L'expérience compte pour 30%
            availability_score * 0.2       # La disponibilité compte pour 20%
        )
        
        recommendations.append({
            "user": collaborator,
            "compatibility_score": round(final_score, 2),
            "skill_score": round(skills_score, 2),
            "experience_score": round(experience_score, 2),
            "availability_score": round(availability_score, 2)
        })
    
    recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return list(recommendations)
```

```python
def calculate_experience_rmse(user1, user2):
    """
    Calcule un score de compatibilité basé sur l'expérience globale
    """
    experience_levels = {
        "Junior": 1,
        "Intermediate": 2,
        "Senior": 3,
        "Expert": 4
    }
    
    level1 = experience_levels.get(user1["experience_level"], 2)
    level2 = experience_levels.get(user2["experience_level"], 2)
    
    years1 = min(user1["years_experience"] / 2, 5)  # Cap à 10 ans -> 5 points
    years2 = min(user2["years_experience"] / 2, 5)
    
    squared_diff_sum = (level1 - level2) ** 2 + (years1 - years2) ** 2
    rmse = math.sqrt(squared_diff_sum / 2)
    
    max_rmse = math.sqrt(25)  # Différence maximale possible
    experience_score = 100 * (1 - (rmse / max_rmse))
    
    return max(0, experience_score)
```


```python
def calculate_rmse_score(user1_skills, user2_skills):
    """
    Calcule le score RMSE entre les compétences de deux utilisateurs.
    Plus le score est bas, plus les utilisateurs sont compatibles.
    """
    squared_diff_sum = 0
    total_comparisons = 0
    
    for domain, skills1 in user1_skills.items():
        if domain in user2_skills:
            skills2 = user2_skills[domain]
            
            # Créer des dictionnaires pour un accès facile
            skills2_dict = {skill["name"]: skill for skill in skills2["skills"]}
            
            for skill1 in skills1["skills"]:
                if skill1["name"] in skills2_dict:
                    skill2 = skills2_dict[skill1["name"]]
                    
                    # Calculer la différence au carré pour le niveau
                    level_diff = (skill1["level"] - skill2["level"]) ** 2
                    
                    # Calculer la différence au carré pour les années d'expérience (normalisé sur 5)
                    exp1 = min(skill1["years_experience"] / 2, 5)  # Cap à 10 ans -> 5 points
                    exp2 = min(skill2["years_experience"] / 2, 5)
                    exp_diff = (exp1 - exp2) ** 2
                    
                    # Ajouter les différences au total
                    squared_diff_sum += level_diff + exp_diff
                    total_comparisons += 2  # Car on compte niveau et expérience
    
    if total_comparisons == 0:
        return 100  # Score maximum si aucune compétence en commun
        
    rmse = math.sqrt(squared_diff_sum / total_comparisons)
    
    # Convertir le RMSE en score de compatibilité (0-100)
    # Plus le RMSE est bas, plus le score est élevé
    max_rmse = math.sqrt(25)  # Différence maximale possible (5^2)
    compatibility_score = 100 * (1 - (rmse / max_rmse))
    
    return max(0, compatibility_score)  # Garantir un score positif
```