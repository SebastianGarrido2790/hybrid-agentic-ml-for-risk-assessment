"""
OpenTelemetry Tracing Configuration.

This module initializes OpenTelemetry tracing for the ACRAS system,
using the gen_ai.* semantic conventions for LLM tracking.
"""

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def configure_tracer(service_name: str = "acras", environment: str = "production"):
    """
    Configure and return an OpenTelemetry Tracer.
    Includes an OTLP exporter for external collection.
    """
    resource = Resource.create(
        attributes={
            "service.name": service_name,
            "deployment.environment": environment,
        }
    )

    provider = TracerProvider(resource=resource)

    # Configure exporters
    # In tests, we might want to skip exporting
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or not os.environ.get("TESTING"):
        otlp_exporter = OTLPSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    if os.environ.get("DEBUG_TELEMETRY"):
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)
