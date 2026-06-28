from apps.common.events import EventDispatcher, MatchCreatedEvent, MatchStartedEvent, MatchFinishedEvent
from apps.games.selectors import MatchSelector
from .models import MatchMetric, GamePopularityMetric

def handle_match_created(event: MatchCreatedEvent):
    pop, _ = GamePopularityMetric.objects.get_or_create(game_id=event.game_id)
    pop.total_matches += 1
    pop.save()

def handle_match_started(event: MatchStartedEvent):
    match = MatchSelector.get_match(event.match_id)
    if not match: return
    
    players_count = len(MatchSelector.get_players(match))
    
    MatchMetric.objects.create(
        match_id=event.match_id,
        game_id=str(match.game.id),
        started_at=event.timestamp,
        players_at_start=players_count
    )
    
    pop, _ = GamePopularityMetric.objects.get_or_create(game_id=str(match.game.id))
    pop.total_players += players_count
    pop.save()

def handle_match_finished(event: MatchFinishedEvent):
    try:
        metric = MatchMetric.objects.get(match_id=event.match_id)
    except MatchMetric.DoesNotExist:
        return
        
    match = MatchSelector.get_match(event.match_id)
    if not match: return
    
    players_count = len(MatchSelector.get_players(match))
    metric.finished_at = event.timestamp
    metric.players_at_finish = players_count
    metric.calculate_duration()
    metric.calculate_quit_rate()
    metric.save()

def register_subscribers():
    EventDispatcher.subscribe(MatchCreatedEvent, handle_match_created)
    EventDispatcher.subscribe(MatchStartedEvent, handle_match_started)
    EventDispatcher.subscribe(MatchFinishedEvent, handle_match_finished)
