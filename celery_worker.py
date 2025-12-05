# Blueprint version for deploying your multi-service architecture
services:
  # 1. WEB SERVICE (Handles HTTP requests via Gunicorn)
  - type: web
    name: website-quality-check-web
    env: python
    region: us-east
    plan: starter # Starter plan recommended for a full production stack
    buildCommand: "pip install -r requirements.txt"
    # IMPORTANT: Use the command from your Procfile which points to wsgi.py
    startCommand: "gunicorn wsgi:application" 
    envVars:
      - key: CELERY_BROKER_URL
        fromService:
          type: keyvalue
          name: celery-broker
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: keyvalue
          name: celery-broker
      - key: PYTHONUNBUFFERED
        value: "1" 
      # Add your necessary secrets here
      - key: SECRET_KEY
        generateValue: true

  # 2. CELERY WORKER SERVICE (Executes the actual tasks)
  - type: worker
    name: website-celery-worker
    env: python
    region: us-east
    plan: starter # Starter plan recommended for a worker
    buildCommand: "pip install -r requirements.txt"
    # CRITICAL: Starts the worker process, targeting the celery_app object in the app module
    startCommand: "celery -A app.celery_app worker --loglevel info"
    envVars:
      - key: CELERY_BROKER_URL
        fromService:
          type: keyvalue
          name: celery-broker
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: keyvalue
          name: celery-broker

  # 3. CELERY BEAT SERVICE (Runs the scheduler/crontab)
  - type: worker
    name: website-celery-beat
    env: python
    region: us-east
    plan: starter
    buildCommand: "pip install -r requirements.txt"
    # CRITICAL: Starts the beat process, using the beat schedule defined in celery_worker.py
    startCommand: "celery -A app.celery_app beat -S celery_worker.CeleryBeatScheduler --loglevel info"
    envVars:
      - key: CELERY_BROKER_URL
        fromService:
          type: keyvalue
          name: celery-broker
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: keyvalue
          name: celery-broker

# 4. DATA STORE (Redis/Key Value for Celery Broker)
keyvalues:
  - name: celery-broker
    plan: starter # Starter plan provides persistence, recommended for queues
    region: us-east
    maxmemoryPolicy: noeviction
