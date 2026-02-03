"""
Distributed Tracing with OpenTelemetry
"""
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

class DistributedTracing:
    def __init__(self):
        # Initialize tracer
        trace.set_tracer_provider(TracerProvider())
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name="jaeger",
            agent_port=6831,
        )
        
        # Add span processor
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        
        self.tracer = trace.get_tracer(__name__)

    async def trace_operation(
        self,
        operation_name: str,
        parent_context: Optional[Any] = None,
        **attributes
    ):
        """Create trace for operation"""
        with self.tracer.start_as_current_span(
            operation_name,
            context=parent_context
        ) as span:
            # Add attributes
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            yield span

    def instrument_fastapi(self, app):
        """Instrument FastAPI application"""
        FastAPIInstrumentor.instrument_app(app)
