from api.graphql.resolvers import resolvers
from ariadne import load_schema_from_path, make_executable_schema
from core import config
from db.base import get_session
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from patisson_errors.fastapi import validation_exception_handler
from patisson_graphql.fastapi_handlers.api import graphql_server

type_defs = load_schema_from_path("app/api/graphql/schema.graphql")
schema = make_executable_schema(type_defs, resolvers)


trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: config.SERVICE_NAME})
    )
)
jaeger_exporter = JaegerExporter()
trace.get_tracer_provider().add_span_processor(  # type: ignore[reportAttributeAccessIssue]
    BatchSpanProcessor(jaeger_exporter)
)


app = FastAPI(title=SERVICE_NAME)
FastAPIInstrumentor.instrument_app(app)
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[reportArgumentType]


@app.post("/graphql")
async def graphql_route(request: Request):
    return await graphql_server(
        request=request, 
        schema=schema, 
        session_gen=get_session()
    )
    
app.add_route("/graphql", graphql_route)   # type: ignore[reportArgumentType]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.SERVICE_HOST, port=config.SERVICE_PORT)