from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OrganizationSerializer


class MyOrganizationView(APIView):
    """
    GET/PATCH the requesting user's own organization -- this is where an
    org admin sets their country, which in turn drives which payment
    method the billing page recommends as the sensible local default.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        if org is None:
            return Response({"detail": "Not linked to an organization."}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrganizationSerializer(org).data)

    def patch(self, request):
        user = request.user
        if user.role != "admin" or user.organization is None:
            return Response(
                {"detail": "Only your organization's admin can edit company details."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OrganizationSerializer(user.organization, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
